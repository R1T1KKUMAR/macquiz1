import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from '../context/ToastContext';
import { quizAPI, questionBankAPI, subjectAPI } from '../services/api';
import {
    Plus, X, Save, Trash2, Copy, ChevronUp, ChevronDown,
    FileText, Clock, Award, AlertCircle, CheckCircle, Sparkles
} from 'lucide-react';

const QuizCreator = ({ embedded = false, onDone, quizIdOverride = null }) => {
    const navigate = useNavigate();
    const { quizId } = useParams();
    const { success, error } = useToast();
    const effectiveQuizId = quizIdOverride ?? quizId;
    const isEditMode = !!effectiveQuizId;
    
    const [quizData, setQuizData] = useState({
        title: '',
        description: '',
        department: '',
        class_year: '1st Year',
        duration_minutes: 30,
        marks_per_correct: 1,
        negative_marking: 0.25,
        is_active: false,
        questions: []
    });

    const [currentQuestion, setCurrentQuestion] = useState({
        question_text: '',
        question_type: 'mcq',
        option_a: '',
        option_b: '',
        option_c: '',
        option_d: '',
        correct_answer: '',
        marks: 1
    });

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showQuestionForm, setShowQuestionForm] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [subjects, setSubjects] = useState([]);
    const [isGeneratingAI, setIsGeneratingAI] = useState(false);
    const [aiGeneration, setAiGeneration] = useState({
        topic: '',
        difficulty: 'medium',
        question_type: 'mcq',
        count: 1,
        marks: 1,
        subject_id: '',
        save_to_bank: false,
    });

    const loadQuizData = useCallback(async () => {
        setIsLoading(true);
        try {
            const quiz = await quizAPI.getQuiz(effectiveQuizId);
            setQuizData({
                title: quiz.title || '',
                description: quiz.description || '',
                department: quiz.department || '',
                class_year: quiz.class_year || '1st Year',
                duration_minutes: quiz.duration_minutes ?? 30,
                marks_per_correct: quiz.marks_per_correct ?? 1,
                negative_marking: quiz.negative_marking ?? 0.25,
                is_active: quiz.is_active || false,
                questions: quiz.questions || []
            });
        } catch (err) {
            console.error('Failed to load quiz:', err);
            error(err.data?.detail || 'Failed to load quiz data');
            navigate('/dashboard');
        } finally {
            setIsLoading(false);
        }
    }, [effectiveQuizId, error, navigate]);

    // Load quiz data in edit mode
    useEffect(() => {
        if (isEditMode) {
            loadQuizData();
        }
    }, [isEditMode, loadQuizData]);

    useEffect(() => {
        const loadSubjects = async () => {
            try {
                const data = await subjectAPI.getAllSubjects(true);
                setSubjects(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error('Failed to load subjects:', err);
            }
        };
        loadSubjects();
    }, []);

    const departments = [
        'Computer Science Engg.',
        'Artificial Intelligence',
        'Mechanical Engineering',
        'Electrical Engineering',
        'Mathematics',
        'Physics'
    ];

    const years = ['1st Year', '2nd Year', '3rd Year', '4th Year'];

    const handleQuizChange = (e) => {
        const { name, value } = e.target;
        setQuizData({ ...quizData, [name]: value });
    };

    const handleQuestionChange = (e) => {
        const { name, value } = e.target;
        setCurrentQuestion({ ...currentQuestion, [name]: value });
    };

    const handleAIChange = (e) => {
        const { name, value, type, checked } = e.target;
        setAiGeneration((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleGenerateWithAI = async () => {
        const topic = aiGeneration.topic.trim();
        if (!topic) {
            error('Please enter a topic for AI question generation.');
            return;
        }

        if (aiGeneration.save_to_bank && !aiGeneration.subject_id) {
            error('Please select a subject to save generated questions into question bank.');
            return;
        }

        setIsGeneratingAI(true);
        try {
            const payload = {
                topic,
                difficulty: aiGeneration.difficulty,
                question_type: aiGeneration.question_type,
                count: Number(aiGeneration.count) || 1,
                marks: Number(aiGeneration.marks) || 1,
                save_to_bank: Boolean(aiGeneration.save_to_bank),
            };

            if (aiGeneration.subject_id) {
                payload.subject_id = Number(aiGeneration.subject_id);
            }

            const response = await questionBankAPI.generateQuestions(payload);
            const generated = Array.isArray(response?.questions) ? response.questions : [];

            if (!generated.length) {
                error('AI could not generate questions. Please try different inputs.');
                return;
            }

            const mappedQuestions = generated
                .filter((q) => q?.question_type === 'mcq' || q?.question_type === 'true_false')
                .map((q) => ({
                    id: Date.now() + Math.floor(Math.random() * 100000),
                    question_text: q.question_text || '',
                    question_type: q.question_type,
                    option_a: q.option_a || '',
                    option_b: q.option_b || '',
                    option_c: q.option_c || '',
                    option_d: q.option_d || '',
                    correct_answer: q.correct_answer || '',
                    marks: Number(q.marks) || Number(aiGeneration.marks) || 1,
                }));

            if (!mappedQuestions.length) {
                error('Generated questions are not compatible with this quiz editor. Try MCQ or True/False.');
                return;
            }

            setQuizData((prev) => ({
                ...prev,
                questions: [...prev.questions, ...mappedQuestions],
            }));

            const saveMsg = response?.saved_count
                ? ` and saved ${response.saved_count} to question bank`
                : '';
            const providerMsg = response?.fallback_used ? ' (fallback mode)' : '';
            success(`Added ${mappedQuestions.length} AI question(s) to this quiz${saveMsg}${providerMsg}.`);
        } catch (err) {
            console.error('AI generation failed:', err);
            error(err?.data?.detail || err?.message || 'Failed to generate AI questions');
        } finally {
            setIsGeneratingAI(false);
        }
    };

    const addQuestion = () => {
        if (!currentQuestion.question_text.trim()) {
            error('Please enter a question');
            return;
        }

        if (currentQuestion.question_type === 'mcq') {
            if (!currentQuestion.option_a || !currentQuestion.option_b) {
                error('Please provide at least 2 options for MCQ');
                return;
            }
            if (!currentQuestion.correct_answer) {
                error('Please select the correct answer');
                return;
            }
        }

        if (currentQuestion.question_type === 'true_false' && !currentQuestion.correct_answer) {
            error('Please select the correct answer');
            return;
        }

        const newQuestion = { ...currentQuestion, id: Date.now() };

        if (editingIndex !== null) {
            const updatedQuestions = [...quizData.questions];
            updatedQuestions[editingIndex] = newQuestion;
            setQuizData({ ...quizData, questions: updatedQuestions });
            success('Question updated successfully');
            setEditingIndex(null);
        } else {
            setQuizData({
                ...quizData,
                questions: [...quizData.questions, newQuestion]
            });
            success('Question added successfully');
        }

        resetQuestionForm();
        setShowQuestionForm(false);
    };

    const editQuestion = (index) => {
        setCurrentQuestion(quizData.questions[index]);
        setEditingIndex(index);
        setShowQuestionForm(true);
    };

    const deleteQuestion = (index) => {
        if (window.confirm('Are you sure you want to delete this question?')) {
            const updatedQuestions = quizData.questions.filter((_, i) => i !== index);
            setQuizData({ ...quizData, questions: updatedQuestions });
            success('Question deleted');
        }
    };

    const duplicateQuestion = (index) => {
        const duplicated = { ...quizData.questions[index], id: Date.now() };
        const updatedQuestions = [...quizData.questions];
        updatedQuestions.splice(index + 1, 0, duplicated);
        setQuizData({ ...quizData, questions: updatedQuestions });
        success('Question duplicated');
    };

    const moveQuestion = (index, direction) => {
        const newIndex = direction === 'up' ? index - 1 : index + 1;
        if (newIndex < 0 || newIndex >= quizData.questions.length) return;

        const updatedQuestions = [...quizData.questions];
        [updatedQuestions[index], updatedQuestions[newIndex]] = 
        [updatedQuestions[newIndex], updatedQuestions[index]];
        
        setQuizData({ ...quizData, questions: updatedQuestions });
    };

    const resetQuestionForm = () => {
        setCurrentQuestion({
            question_text: '',
            question_type: 'mcq',
            option_a: '',
            option_b: '',
            option_c: '',
            option_d: '',
            correct_answer: '',
            marks: 1
        });
        setEditingIndex(null);
    };

    const handleSubmitQuiz = async () => {
        if (!quizData.title.trim()) {
            error('Please enter quiz title');
            return;
        }

        if (quizData.questions.length === 0) {
            error('Please add at least one question');
            return;
        }

        setIsSubmitting(true);
        try {
            const formattedQuestions = quizData.questions.map(q => ({
                question_text: q.question_text,
                question_type: q.question_type,
                option_a: q.option_a || null,
                option_b: q.option_b || null,
                option_c: q.option_c || null,
                option_d: q.option_d || null,
                correct_answer: q.correct_answer,
                marks: q.marks
            }));

            const parsedDuration = Number.parseInt(quizData.duration_minutes, 10);
            const parsedMarksPerCorrect = Number.parseFloat(quizData.marks_per_correct);
            const parsedNegativeMarking = Number.parseFloat(quizData.negative_marking);

            const payload = {
                title: quizData.title,
                description: quizData.description || null,
                duration_minutes: Number.isFinite(parsedDuration) ? parsedDuration : 30,
                marks_per_correct: Number.isFinite(parsedMarksPerCorrect) ? parsedMarksPerCorrect : 1,
                negative_marking: Number.isFinite(parsedNegativeMarking) ? parsedNegativeMarking : 0.25,
                questions: formattedQuestions
            };

            // Only set is_active for NEW quizzes (not when editing)
            if (!isEditMode) {
                payload.is_active = false; // New quizzes start as inactive
            }

            // Only add department and class_year if they have values
            if (quizData.department && quizData.department.trim() !== '') {
                payload.department = quizData.department;
            }
            if (quizData.class_year && quizData.class_year.trim() !== '') {
                payload.class_year = quizData.class_year;
            }

            if (isEditMode) {
                await quizAPI.updateQuiz(effectiveQuizId, payload);
                success('Quiz updated successfully!');
            } else {
                const createdQuiz = await quizAPI.createQuiz(payload);
                if (createdQuiz?.id && createdQuiz?.is_active) {
                    await quizAPI.updateQuiz(createdQuiz.id, { is_active: false });
                }
                success('Quiz created successfully!');
            }
            if (onDone) {
                onDone();
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            console.error('Quiz creation error:', err);
            console.error('Error details:', err.data);
            error(err.data?.detail || err.message || 'Failed to create quiz');
        } finally {
            setIsSubmitting(false);
        }
    };

    const totalMarks = quizData.questions.reduce((sum, q) => sum + (q.marks || 0), 0);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600 text-lg">Loading quiz data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className={`${embedded ? '' : 'min-h-screen'} bg-gradient-to-br from-blue-50 to-indigo-50 py-4 sm:py-8`}>
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 md:p-8 mb-6">
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                        {isEditMode ? 'Edit Quiz' : 'Create New Quiz'}
                    </h1>
                    <p className="text-gray-600">
                        {isEditMode ? 'Update your quiz details and questions' : 'Set up your quiz details and add questions'}
                    </p>
                </div>

                {/* Quiz Details */}
                <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 md:p-8 mb-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                        <FileText className="mr-2 text-blue-600" size={24} />
                        Quiz Details
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Quiz Title *
                            </label>
                            <input
                                type="text"
                                name="title"
                                value={quizData.title}
                                onChange={handleQuizChange}
                                placeholder="Enter quiz title"
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Description
                            </label>
                            <textarea
                                name="description"
                                value={quizData.description}
                                onChange={handleQuizChange}
                                rows="3"
                                placeholder="Brief description of the quiz"
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Department
                            </label>
                            <select
                                name="department"
                                value={quizData.department}
                                onChange={handleQuizChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">All Departments</option>
                                {departments.map(dept => (
                                    <option key={dept} value={dept}>{dept}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Class/Year
                            </label>
                            <select
                                name="class_year"
                                value={quizData.class_year}
                                onChange={handleQuizChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">All Years</option>
                                {years.map(year => (
                                    <option key={year} value={year}>{year}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Duration (minutes) *
                            </label>
                            <input
                                type="number"
                                name="duration_minutes"
                                value={quizData.duration_minutes}
                                onChange={handleQuizChange}
                                min="1"
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Marks Per Correct Answer
                            </label>
                            <input
                                type="number"
                                step="0.25"
                                min="0"
                                name="marks_per_correct"
                                value={quizData.marks_per_correct}
                                onChange={handleQuizChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Negative Marking (per wrong answer)
                            </label>
                            <input
                                type="number"
                                step="0.25"
                                min="0"
                                name="negative_marking"
                                value={quizData.negative_marking}
                                onChange={handleQuizChange}
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                Example: enter 0.25 to deduct 0.25 marks for each incorrect answer.
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Total Marks: <span className="text-blue-600 font-bold">{totalMarks}</span>
                            </label>
                            <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl text-gray-600">
                                Calculated from questions
                            </div>
                        </div>
                    </div>
                </div>

                {/* Questions Section */}
                <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 md:p-8 mb-6">
                    <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 mb-6">
                        <h2 className="text-xl font-bold text-gray-900 flex items-center">
                            <Award className="mr-2 text-blue-600" size={24} />
                            Questions ({quizData.questions.length})
                        </h2>
                        <button
                            onClick={() => {
                                resetQuestionForm();
                                setShowQuestionForm(true);
                            }}
                            className="w-full sm:w-auto justify-center flex items-center px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition shadow-lg"
                        >
                            <Plus size={20} className="mr-2" />
                            Add Question
                        </button>
                    </div>

                    <div className="mb-6 p-4 border border-indigo-200 bg-indigo-50 rounded-xl">
                        <div className="flex items-center mb-3">
                            <Sparkles size={18} className="text-indigo-600 mr-2" />
                            <h3 className="text-sm font-bold text-indigo-900">AI Question Generator</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                            <input
                                type="text"
                                name="topic"
                                value={aiGeneration.topic}
                                onChange={handleAIChange}
                                placeholder="Topic (e.g., OOP in Java)"
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            />

                            <select
                                name="question_type"
                                value={aiGeneration.question_type}
                                onChange={handleAIChange}
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            >
                                <option value="mcq">MCQ</option>
                                <option value="true_false">True/False</option>
                            </select>

                            <select
                                name="difficulty"
                                value={aiGeneration.difficulty}
                                onChange={handleAIChange}
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            >
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>

                            <input
                                type="number"
                                name="count"
                                min="1"
                                max="10"
                                value={aiGeneration.count}
                                onChange={handleAIChange}
                                placeholder="Count"
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            />

                            <input
                                type="number"
                                name="marks"
                                min="0.25"
                                step="0.25"
                                value={aiGeneration.marks}
                                onChange={handleAIChange}
                                placeholder="Marks"
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            />

                            <select
                                name="subject_id"
                                value={aiGeneration.subject_id}
                                onChange={handleAIChange}
                                className="px-3 py-2 border border-indigo-200 rounded-lg bg-white"
                            >
                                <option value="">Subject (optional)</option>
                                {subjects.map((subject) => (
                                    <option key={subject.id} value={subject.id}>{subject.name}</option>
                                ))}
                            </select>

                            <label className="flex items-center px-3 py-2 border border-indigo-200 rounded-lg bg-white text-sm text-indigo-900">
                                <input
                                    type="checkbox"
                                    name="save_to_bank"
                                    checked={aiGeneration.save_to_bank}
                                    onChange={handleAIChange}
                                    className="mr-2"
                                />
                                Save to Question Bank
                            </label>

                            <button
                                type="button"
                                onClick={handleGenerateWithAI}
                                disabled={isGeneratingAI}
                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-60"
                            >
                                {isGeneratingAI ? 'Generating...' : 'Generate with AI'}
                            </button>
                        </div>

                        <p className="mt-2 text-xs text-indigo-700">
                            Generated questions are added directly to this quiz. Enable Save to Question Bank to store reusable copies.
                        </p>
                    </div>

                    {/* Question List */}
                    {quizData.questions.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <AlertCircle size={48} className="mx-auto mb-4 text-gray-400" />
                            <p className="text-lg">No questions added yet</p>
                            <p className="text-sm">Click "Add Question" to create your first question</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {quizData.questions.map((q, index) => (
                                <div key={q.id} className="border-2 border-gray-200 rounded-xl p-4 sm:p-6 hover:border-blue-300 transition">
                                    <div className="flex flex-col sm:flex-row justify-between sm:items-start gap-3 mb-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-bold">
                                                    Q{index + 1}
                                                </span>
                                                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-bold">
                                                    {q.marks} {q.marks === 1 ? 'Mark' : 'Marks'}
                                                </span>
                                                <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-bold uppercase">
                                                    {q.question_type.replace('_', ' ')}
                                                </span>
                                            </div>
                                            <p className="text-lg font-semibold text-gray-900">{q.question_text}</p>
                                        </div>
                                        <div className="flex items-center flex-wrap gap-2 sm:ml-4">
                                            <button
                                                onClick={() => moveQuestion(index, 'up')}
                                                disabled={index === 0}
                                                className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-30"
                                            >
                                                <ChevronUp size={20} />
                                            </button>
                                            <button
                                                onClick={() => moveQuestion(index, 'down')}
                                                disabled={index === quizData.questions.length - 1}
                                                className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-30"
                                            >
                                                <ChevronDown size={20} />
                                            </button>
                                            <button
                                                onClick={() => duplicateQuestion(index)}
                                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                                            >
                                                <Copy size={20} />
                                            </button>
                                            <button
                                                onClick={() => editQuestion(index)}
                                                className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg font-semibold"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => deleteQuestion(index)}
                                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                                            >
                                                <Trash2 size={20} />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Display Options */}
                                    {q.question_type === 'mcq' && (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                                            {['A', 'B', 'C', 'D'].map((opt) => {
                                                const optKey = `option_${opt.toLowerCase()}`;
                                                const optText = q[optKey];
                                                if (!optText) return null;
                                                const isCorrect = q.correct_answer === opt;
                                                return (
                                                    <div
                                                        key={opt}
                                                        className={`p-3 rounded-lg border-2 ${
                                                            isCorrect
                                                                ? 'border-green-400 bg-green-50'
                                                                : 'border-gray-200 bg-gray-50'
                                                        }`}
                                                    >
                                                        <div className="flex items-center">
                                                            <span className="font-bold text-gray-700 mr-2">{opt}.</span>
                                                            <span className="text-gray-900">{optText}</span>
                                                            {isCorrect && (
                                                                <CheckCircle size={18} className="ml-auto text-green-600" />
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}

                                    {q.question_type === 'true_false' && (
                                        <div className="mt-4">
                                            <span className="text-sm text-gray-600">Correct Answer: </span>
                                            <span className="font-bold text-green-600">{q.correct_answer}</span>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Question Form Modal */}
                {showQuestionForm && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 overflow-y-auto">
                        <div className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full my-4 sm:my-8 max-h-[92vh] overflow-y-auto">
                            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 sm:p-6 rounded-t-3xl">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-xl sm:text-2xl font-bold">
                                        {editingIndex !== null ? 'Edit Question' : 'Add New Question'}
                                    </h3>
                                    <button
                                        onClick={() => {
                                            setShowQuestionForm(false);
                                            resetQuestionForm();
                                        }}
                                        className="p-2 hover:bg-white/20 rounded-full transition"
                                    >
                                        <X size={24} />
                                    </button>
                                </div>
                            </div>

                            <div className="p-4 sm:p-6 md:p-8 space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Question Type
                                    </label>
                                    <select
                                        name="question_type"
                                        value={currentQuestion.question_type}
                                        onChange={handleQuestionChange}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="mcq">Multiple Choice (MCQ)</option>
                                        <option value="true_false">True/False</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Question Text *
                                    </label>
                                    <textarea
                                        name="question_text"
                                        value={currentQuestion.question_text}
                                        onChange={handleQuestionChange}
                                        rows="3"
                                        placeholder="Enter your question here..."
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>

                                {currentQuestion.question_type === 'mcq' && (
                                    <>
                                        <div className="grid grid-cols-1 gap-4">
                                            {['A', 'B', 'C', 'D'].map((opt) => (
                                                <div key={opt}>
                                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                                        Option {opt} {opt === 'A' || opt === 'B' ? '*' : ''}
                                                    </label>
                                                    <input
                                                        type="text"
                                                        name={`option_${opt.toLowerCase()}`}
                                                        value={currentQuestion[`option_${opt.toLowerCase()}`]}
                                                        onChange={handleQuestionChange}
                                                        placeholder={`Enter option ${opt}`}
                                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                Correct Answer *
                                            </label>
                                            <select
                                                name="correct_answer"
                                                value={currentQuestion.correct_answer}
                                                onChange={handleQuestionChange}
                                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            >
                                                <option value="">Select correct answer</option>
                                                {['A', 'B', 'C', 'D'].map((opt) => 
                                                    currentQuestion[`option_${opt.toLowerCase()}`] && (
                                                        <option key={opt} value={opt}>
                                                            {opt} - {currentQuestion[`option_${opt.toLowerCase()}`]}
                                                        </option>
                                                    )
                                                )}
                                            </select>
                                        </div>
                                    </>
                                )}

                                {currentQuestion.question_type === 'true_false' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Correct Answer *
                                        </label>
                                        <select
                                            name="correct_answer"
                                            value={currentQuestion.correct_answer}
                                            onChange={handleQuestionChange}
                                            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        >
                                            <option value="">Select correct answer</option>
                                            <option value="True">True</option>
                                            <option value="False">False</option>
                                        </select>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Marks *
                                    </label>
                                    <input
                                        type="number"
                                        name="marks"
                                        value={currentQuestion.marks}
                                        onChange={handleQuestionChange}
                                        min="1"
                                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>

                                <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 sm:space-x-4 pt-4">
                                    <button
                                        onClick={() => {
                                            setShowQuestionForm(false);
                                            resetQuestionForm();
                                        }}
                                        className="w-full sm:w-auto px-6 py-3 border-2 border-gray-300 rounded-xl text-gray-700 font-semibold hover:bg-gray-100 transition"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={addQuestion}
                                        className="w-full sm:w-auto justify-center flex items-center px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition shadow-lg"
                                    >
                                        <Save size={20} className="mr-2" />
                                        {editingIndex !== null ? 'Update' : 'Add'} Question
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Submit Quiz */}
                <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 md:p-8">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                        <div>
                            <h3 className="text-xl font-bold text-gray-900 mb-2">Ready to Publish?</h3>
                            <p className="text-gray-600">
                                {quizData.questions.length} question(s) • {totalMarks} total marks • {quizData.duration_minutes} minutes
                            </p>
                        </div>
                        <button
                            onClick={handleSubmitQuiz}
                            disabled={isSubmitting || quizData.questions.length === 0}
                            className="w-full sm:w-auto justify-center flex items-center px-8 py-4 bg-green-600 text-white rounded-xl font-bold text-base sm:text-lg hover:bg-green-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? (
                                <>
                                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                                    {isEditMode ? 'Updating...' : 'Creating...'}
                                </>
                            ) : (
                                <>
                                    <CheckCircle size={24} className="mr-3" />
                                    {isEditMode ? 'Update Quiz' : 'Create Quiz'}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default QuizCreator;
