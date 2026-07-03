from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import urllib.request
import urllib.error
from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.models.models import QuestionBank, User, Subject
from app.schemas.schemas import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankResponse,
    QuestionFilter,
    AIQuestionGenerateRequest,
    AIQuestionGenerateResponse,
)

router = APIRouter()


def _fallback_generate_questions(payload: AIQuestionGenerateRequest) -> List[dict]:
    questions = []
    topic = payload.topic.strip()

    for idx in range(1, payload.count + 1):
        if payload.question_type == "mcq":
            questions.append(
                {
                    "question_text": f"[{payload.difficulty.title()}] {topic}: Which option best explains concept {idx}?",
                    "question_type": "mcq",
                    "option_a": f"Core principle of {topic}",
                    "option_b": f"Common misconception about {topic}",
                    "option_c": f"Unrelated statement about {topic}",
                    "option_d": f"Advanced edge case in {topic}",
                    "correct_answer": "A",
                    "topic": topic,
                    "difficulty": payload.difficulty,
                    "marks": payload.marks,
                }
            )
        elif payload.question_type == "true_false":
            truth_value = "True" if idx % 2 else "False"
            statement = (
                f"{topic} always requires sequential processing."
                if truth_value == "False"
                else f"{topic} can be evaluated using measurable criteria."
            )
            questions.append(
                {
                    "question_text": f"[{payload.difficulty.title()}] {statement}",
                    "question_type": "true_false",
                    "option_a": None,
                    "option_b": None,
                    "option_c": None,
                    "option_d": None,
                    "correct_answer": truth_value,
                    "topic": topic,
                    "difficulty": payload.difficulty,
                    "marks": payload.marks,
                }
            )
        else:
            questions.append(
                {
                    "question_text": f"[{payload.difficulty.title()}] Briefly explain {topic} with one practical example ({idx}).",
                    "question_type": "short_answer",
                    "option_a": None,
                    "option_b": None,
                    "option_c": None,
                    "option_d": None,
                    "correct_answer": f"A correct response should define {topic} and include one valid practical example.",
                    "topic": topic,
                    "difficulty": payload.difficulty,
                    "marks": payload.marks,
                }
            )

    return questions


def _extract_json_object(raw_text: str) -> Optional[dict]:
    if not raw_text:
        return None
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(raw_text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _generate_questions_with_gemini(payload: AIQuestionGenerateRequest) -> Optional[List[dict]]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not settings.AI_ENABLED or not api_key:
        return None

    prompt = (
        "Generate high-quality assessment questions as strict JSON. "
        "Return an object with key questions containing an array. "
        "Each item must include question_text, question_type, option_a, option_b, option_c, option_d, "
        "correct_answer, topic, difficulty, marks. "
        "For true_false, set options to null and correct_answer to True or False. "
        "For short_answer, options should be null and correct_answer should be concise marking guidance.\n\n"
        f"topic: {payload.topic}\n"
        f"difficulty: {payload.difficulty}\n"
        f"question_type: {payload.question_type}\n"
        f"count: {payload.count}\n"
        f"marks: {payload.marks}\n"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )
    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw_body = response.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None

    try:
        parsed = json.loads(raw_body)
        content_text = parsed["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    parsed_output = _extract_json_object(content_text)
    if not parsed_output:
        return None

    questions = parsed_output.get("questions")
    if not isinstance(questions, list) or not questions:
        return None

    normalized = []
    for item in questions[: payload.count]:
        if not isinstance(item, dict):
            continue

        question_text = str(item.get("question_text") or "").strip()
        question_type = str(item.get("question_type") or payload.question_type).strip().lower()
        correct_answer = str(item.get("correct_answer") or "").strip()
        if not question_text or not correct_answer:
            continue

        normalized.append(
            {
                "question_text": question_text,
                "question_type": question_type,
                "option_a": item.get("option_a"),
                "option_b": item.get("option_b"),
                "option_c": item.get("option_c"),
                "option_d": item.get("option_d"),
                "correct_answer": correct_answer,
                "topic": str(item.get("topic") or payload.topic).strip(),
                "difficulty": str(item.get("difficulty") or payload.difficulty).strip().lower(),
                "marks": float(item.get("marks") or payload.marks),
            }
        )

    return normalized or None


def _normalize_generated_questions(payload: AIQuestionGenerateRequest, generated_questions: List[dict]) -> List[dict]:
    normalized_questions = []
    for question in generated_questions:
        question_type = str(question.get("question_type") or payload.question_type).strip().lower()
        if question_type not in {"mcq", "true_false", "short_answer"}:
            question_type = payload.question_type

        difficulty = str(question.get("difficulty") or payload.difficulty).strip().lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = payload.difficulty

        marks = question.get("marks", payload.marks)
        try:
            marks = float(marks)
        except (TypeError, ValueError):
            marks = payload.marks

        cleaned = {
            "question_text": str(question.get("question_text") or "").strip(),
            "question_type": question_type,
            "option_a": question.get("option_a") if question_type == "mcq" else None,
            "option_b": question.get("option_b") if question_type == "mcq" else None,
            "option_c": question.get("option_c") if question_type == "mcq" else None,
            "option_d": question.get("option_d") if question_type == "mcq" else None,
            "correct_answer": str(question.get("correct_answer") or "").strip(),
            "topic": str(question.get("topic") or payload.topic).strip(),
            "difficulty": difficulty,
            "marks": marks,
        }

        if not cleaned["question_text"] or not cleaned["correct_answer"]:
            continue

        if cleaned["question_type"] == "mcq":
            if not cleaned["option_a"] or not cleaned["option_b"]:
                continue
            if cleaned["correct_answer"] not in {"A", "B", "C", "D"}:
                cleaned["correct_answer"] = "A"
        elif cleaned["question_type"] == "true_false":
            if cleaned["correct_answer"].lower() not in {"true", "false"}:
                cleaned["correct_answer"] = "True"
            else:
                cleaned["correct_answer"] = "True" if cleaned["correct_answer"].lower() == "true" else "False"

        normalized_questions.append(cleaned)

    return normalized_questions[: payload.count]


@router.post("/ai/generate", response_model=AIQuestionGenerateResponse)
def generate_questions_with_ai(
    payload: AIQuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"])),
):
    if payload.save_to_bank and not payload.subject_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="subject_id is required when save_to_bank is true",
        )

    if payload.subject_id:
        subject = db.query(Subject).filter(Subject.id == payload.subject_id, Subject.is_active == True).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

    ai_result = _generate_questions_with_gemini(payload)
    fallback_used = ai_result is None
    raw_questions = ai_result if ai_result is not None else _fallback_generate_questions(payload)
    normalized_questions = _normalize_generated_questions(payload, raw_questions)

    if not normalized_questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to generate valid questions",
        )

    saved_count = 0
    output_questions = []

    for question in normalized_questions:
        output_item = {
            **question,
            "saved_to_bank": False,
            "question_bank_id": None,
        }

        if payload.save_to_bank and payload.subject_id:
            db_question = QuestionBank(
                subject_id=payload.subject_id,
                creator_id=current_user.id,
                question_text=question["question_text"],
                question_type=question["question_type"],
                option_a=question["option_a"],
                option_b=question["option_b"],
                option_c=question["option_c"],
                option_d=question["option_d"],
                correct_answer=question["correct_answer"],
                topic=question["topic"],
                difficulty=question["difficulty"],
                marks=question["marks"],
                is_active=True,
            )
            db.add(db_question)
            db.flush()

            output_item["saved_to_bank"] = True
            output_item["question_bank_id"] = db_question.id
            saved_count += 1

        output_questions.append(output_item)

    if payload.save_to_bank and saved_count:
        db.commit()

    return {
        "provider": "gemini" if not fallback_used else "rule-based",
        "model": settings.GEMINI_MODEL if not fallback_used else "deterministic-v1",
        "generated_at": datetime.utcnow(),
        "fallback_used": fallback_used,
        "saved_count": saved_count,
        "questions": output_questions,
    }

@router.post("/", response_model=QuestionBankResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionBankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Add a question to the question bank (Admin and Teacher only)
    """
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == question.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db_question = QuestionBank(
        **question.dict(),
        creator_id=current_user.id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.get("/", response_model=List[QuestionBankResponse])
def get_questions(
    skip: int = 0,
    limit: int = 100,
    subject_id: Optional[int] = None,
    difficulty: Optional[str] = Query(None, regex="^(easy|medium|hard)$"),
    topic: Optional[str] = None,
    question_type: Optional[str] = Query(None, regex="^(mcq|true_false|short_answer)$"),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get questions from question bank with filtering
    """
    query = db.query(QuestionBank)
    
    if active_only:
        query = query.filter(QuestionBank.is_active == True)
    
    if subject_id:
        query = query.filter(QuestionBank.subject_id == subject_id)
    
    if difficulty:
        query = query.filter(QuestionBank.difficulty == difficulty)
    
    if topic:
        query = query.filter(QuestionBank.topic.ilike(f"%{topic}%"))
    
    if question_type:
        query = query.filter(QuestionBank.question_type == question_type)
    
    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/{question_id}", response_model=QuestionBankResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific question from the bank
    """
    question = db.query(QuestionBank).filter(QuestionBank.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question


@router.put("/{question_id}", response_model=QuestionBankResponse)
def update_question(
    question_id: int,
    question_update: QuestionBankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Update a question in the bank (Admin and Teacher only)
    """
    question = db.query(QuestionBank).filter(QuestionBank.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions (creator or admin)
    if current_user.role != "admin" and question.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this question"
        )
    
    # Update fields
    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    from datetime import datetime
    question.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Delete a question from the bank (Admin and Teacher only)
    """
    question = db.query(QuestionBank).filter(QuestionBank.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions (creator or admin)
    if current_user.role != "admin" and question.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this question"
        )
    
    # Soft delete
    question.is_active = False
    db.commit()
    return None


@router.get("/subjects/{subject_id}/topics")
def get_topics_by_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all unique topics for a subject
    """
    from sqlalchemy import func
    
    topics = db.query(QuestionBank.topic).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.is_active == True,
        QuestionBank.topic.isnot(None)
    ).distinct().all()
    
    return {"topics": [topic[0] for topic in topics if topic[0]]}


@router.get("/subjects/{subject_id}/statistics")
def get_subject_question_statistics(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about questions for a subject
    """
    total_questions = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.is_active == True
    ).count()
    
    easy = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.difficulty == "easy",
        QuestionBank.is_active == True
    ).count()
    
    medium = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.difficulty == "medium",
        QuestionBank.is_active == True
    ).count()
    
    hard = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.difficulty == "hard",
        QuestionBank.is_active == True
    ).count()
    
    mcq = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.question_type == "mcq",
        QuestionBank.is_active == True
    ).count()
    
    true_false = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.question_type == "true_false",
        QuestionBank.is_active == True
    ).count()
    
    short_answer = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id,
        QuestionBank.question_type == "short_answer",
        QuestionBank.is_active == True
    ).count()
    
    return {
        "subject_id": subject_id,
        "total_questions": total_questions,
        "by_difficulty": {
            "easy": easy,
            "medium": medium,
            "hard": hard
        },
        "by_type": {
            "mcq": mcq,
            "true_false": true_false,
            "short_answer": short_answer
        }
    }
