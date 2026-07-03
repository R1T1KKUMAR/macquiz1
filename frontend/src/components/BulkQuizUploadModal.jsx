import React, { useState } from 'react';
import { X, Upload, Download, CheckCircle, AlertCircle, FileText, Eye, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../services/api';

const BulkQuizUploadModal = ({ isOpen, onClose, onSuccess }) => {
    const [file, setFile] = useState(null);
    const [validationResults, setValidationResults] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [showPreview, setShowPreview] = useState(false);

    if (!isOpen) return null;

    const parseCSV = (text) => {
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length === 0) return { headers: [], rows: [] };

        const headers = lines[0].split(',').map(h => h.trim());
        const rows = lines.slice(1).map((line, index) => {
            const values = [];
            let currentValue = '';
            let insideQuotes = false;

            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                
                if (char === '"') {
                    insideQuotes = !insideQuotes;
                } else if (char === ',' && !insideQuotes) {
                    values.push(currentValue.trim());
                    currentValue = '';
                } else {
                    currentValue += char;
                }
            }
            values.push(currentValue.trim());

            const row = {};
            headers.forEach((header, i) => {
                row[header] = values[i] || '';
            });
            row._rowNumber = index + 2;
            return row;
        });

        return { headers, rows };
    };

    const validateQuizData = (rows) => {
        const errors = [];
        const warnings = [];
        const validRows = [];
        const quizGroups = {};

        rows.forEach((row) => {
            const rowErrors = [];
            const rowWarnings = [];

            // Check required fields
            if (!row.quiz_title) rowErrors.push('Quiz title is required');
            if (!row.question_text) rowErrors.push('Question text is required');
            if (!row.question_type) rowErrors.push('Question type is required');
            if (!row.correct_answer) rowErrors.push('Correct answer is required');

            // Validate question type (accept both formats)
            const validTypes = ['multiple_choice', 'mcq', 'true_false', 'short_answer'];
            if (row.question_type && !validTypes.includes(row.question_type.toLowerCase())) {
                rowErrors.push('Question type must be multiple_choice (or mcq), true_false, or short_answer');
            }

            // Validate MCQ options
            if (row.question_type === 'multiple_choice' || row.question_type === 'mcq') {
                if (!row.option_a || !row.option_b) {
                    rowErrors.push('Multiple choice questions must have at least options A and B');
                }
            }

            // Validate True/False
            if (row.question_type === 'true_false') {
                if (row.correct_answer && !['true', 'false'].includes(row.correct_answer.toLowerCase())) {
                    rowErrors.push('True/False questions must have correct answer as "true" or "false"');
                }
            }

            // Duration validation
            if (row.duration_minutes && isNaN(parseInt(row.duration_minutes))) {
                rowErrors.push('Duration must be a number');
            }

            // Marks validation
            if (row.marks_per_correct && isNaN(parseFloat(row.marks_per_correct))) {
                rowWarnings.push('Marks per correct should be a number (using default 1)');
            }

            // Group by quiz title
            const quizKey = row.quiz_title?.trim().toLowerCase();
            if (quizKey) {
                if (!quizGroups[quizKey]) {
                    quizGroups[quizKey] = [];
                }
                quizGroups[quizKey].push(row);
            }

            if (rowErrors.length === 0) {
                validRows.push(row);
            }

            if (rowErrors.length > 0 || rowWarnings.length > 0) {
                (rowErrors.length > 0 ? errors : warnings).push({
                    row: row._rowNumber,
                    data: row,
                    issues: rowErrors.length > 0 ? rowErrors : rowWarnings,
                    type: rowErrors.length > 0 ? 'error' : 'warning'
                });
            }
        });

        // Count unique quizzes
        const uniqueQuizzes = Object.keys(quizGroups).length;

        return {
            valid: validRows,
            errors,
            warnings,
            quizGroups,
            uniqueQuizzes,
            totalRows: rows.length,
            validCount: validRows.length,
            errorCount: errors.length,
            warningCount: warnings.length
        };
    };

    const handleFileChange = async (e) => {
        const selectedFile = e.target.files[0];
        if (!selectedFile) return;

        if (!selectedFile.name.endsWith('.csv')) {
            alert('Please upload a CSV file');
            return;
        }

        setFile(selectedFile);
        setIsProcessing(true);

        try {
            const text = await selectedFile.text();
            const { rows } = parseCSV(text);

            const validation = validateQuizData(rows);
            setValidationResults(validation);
            setShowPreview(true);
        } catch (error) {
            alert('Error reading file: ' + error.message);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleUpload = async () => {
        if (!validationResults || validationResults.errorCount > 0) {
            return;
        }

        setIsProcessing(true);
        setUploadProgress(0);

        try {
            const token = localStorage.getItem('access_token');
            
            // Group questions by quiz
            const quizzes = [];
            Object.entries(validationResults.quizGroups).forEach(([_quizKey, questions]) => {
                const firstQ = questions[0];
                const quiz = {
                    title: firstQ.quiz_title,
                    description: firstQ.quiz_description || `Quiz with ${questions.length} questions`,
                    duration_minutes: parseInt(firstQ.duration_minutes) || 30,
                    marks_per_correct: parseFloat(firstQ.marks_per_correct) || 1,
                    negative_marking: parseFloat(firstQ.negative_marking) || 0,
                    is_active: false,
                };
                
                // Only add optional fields if they have valid values
                if (firstQ.subject_id && firstQ.subject_id.trim() !== '' && !isNaN(parseInt(firstQ.subject_id))) {
                    quiz.subject_id = parseInt(firstQ.subject_id);
                }
                
                if (firstQ.department && firstQ.department.trim() !== '') {
                    quiz.department = firstQ.department.trim();
                }
                
                if (firstQ.year && !isNaN(parseInt(firstQ.year))) {
                    quiz.class_year = firstQ.year.toString();
                }
                
                quiz.questions = questions.map((q, idx) => {
                        // Map question_type to backend format
                        const questionType = q.question_type === 'multiple_choice' ? 'mcq' : q.question_type;
                        
                        return {
                            question_text: q.question_text,
                            question_type: questionType,
                            option_a: (questionType === 'mcq') ? q.option_a : null,
                            option_b: (questionType === 'mcq') ? q.option_b : null,
                            option_c: (questionType === 'mcq') ? (q.option_c || null) : null,
                            option_d: (questionType === 'mcq') ? (q.option_d || null) : null,
                            correct_answer: q.correct_answer,
                            marks: parseFloat(firstQ.marks_per_correct) || 1,
                            order: idx
                        };
                    });
                
                quizzes.push(quiz);
            });

            let successCount = 0;
            let failCount = 0;
            const progressStep = 90 / quizzes.length;
            const failedQuizzes = [];

            // Upload each quiz
            for (const quiz of quizzes) {
                try {
                    console.log('Uploading quiz:', quiz.title, quiz);
                    
                    const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(quiz)
                    });

                    if (response.ok) {
                        const createdQuiz = await response.json().catch(() => null);
                        if (createdQuiz?.id && createdQuiz?.is_active) {
                            await fetch(`${API_BASE_URL}/api/v1/quizzes/${createdQuiz.id}`, {
                                method: 'PUT',
                                headers: {
                                    'Authorization': `Bearer ${token}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ is_active: false })
                            });
                        }
                        successCount++;
                        console.log(`✅ Successfully uploaded: ${quiz.title}`);
                    } else {
                        failCount++;
                        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                        const errorMsg = typeof errorData.detail === 'string' 
                            ? errorData.detail 
                            : Array.isArray(errorData.detail)
                            ? errorData.detail.map(e => e.msg || e).join(', ')
                            : JSON.stringify(errorData.detail || errorData);
                        failedQuizzes.push({
                            title: quiz.title,
                            error: errorMsg
                        });
                        console.error(`❌ Failed to upload "${quiz.title}":`, errorData);
                    }
                    setUploadProgress(prev => Math.min(prev + progressStep, 90));
                } catch (error) {
                    failCount++;
                    const errorMsg = error.message === 'Failed to fetch' 
                        ? 'Unable to connect to server. Please ensure the backend is running.'
                        : error.message || 'Network error';
                    failedQuizzes.push({
                        title: quiz.title,
                        error: errorMsg
                    });
                    console.error(`❌ Network error for "${quiz.title}":`, error);
                }
            }

            setUploadProgress(100);

            setTimeout(() => {
                onSuccess({
                    total: quizzes.length,
                    success: successCount,
                    failed: failCount,
                    failedQuizzes
                });
                handleClose();
            }, 500);

        } catch (error) {
            alert('Upload failed: ' + error.message);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setValidationResults(null);
        setShowPreview(false);
        setUploadProgress(0);
        onClose();
    };

    const downloadTemplate = () => {
        const csvContent = `quiz_title,quiz_description,subject_id,duration_minutes,marks_per_correct,negative_marking,passing_marks,is_active,department,year,question_text,question_type,option_a,option_b,option_c,option_d,correct_answer,explanation
    Physics Chapter 1,Basic Physics Concepts,,30,1,0.25,40,false,Science,1st Year,What is the SI unit of force?,multiple_choice,Newton,Joule,Watt,Pascal,A,Force is measured in Newtons (N)
    Physics Chapter 1,Basic Physics Concepts,,30,1,0.25,40,false,Science,1st Year,Is energy conserved in a closed system?,true_false,,,,,true,Law of conservation of energy
    Physics Chapter 1,Basic Physics Concepts,,30,1,0.25,40,false,Science,1st Year,What is the formula for kinetic energy?,multiple_choice,1/2 mv²,mv,mv²,1/2 m²v,A,Kinetic energy = 1/2 × mass × velocity²
    Mathematics Quiz,Algebra Basics,,45,2,0.5,50,false,Mathematics,2nd Year,What is the value of x if 2x + 5 = 15?,multiple_choice,5,10,15,20,A,2x + 5 = 15 → 2x = 10 → x = 5
    Mathematics Quiz,Algebra Basics,,45,2,0.5,50,false,Mathematics,2nd Year,Is (a + b)² = a² + b²?,true_false,,,,,false,(a + b)² = a² + 2ab + b²`;
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bulk_quiz_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const getSummaryColor = () => {
        if (!validationResults) return 'gray';
        if (validationResults.errorCount > 0) return 'red';
        if (validationResults.warningCount > 0) return 'yellow';
        return 'green';
    };

    const canUpload = validationResults && validationResults.errorCount === 0 && validationResults.validCount > 0;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[92vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white p-4 sm:p-6 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
                    <div className="flex items-center space-x-3 min-w-0">
                        <FileText size={28} />
                        <div>
                            <h2 className="text-xl sm:text-2xl font-bold">Bulk Quiz Upload</h2>
                            <p className="text-purple-100 text-sm">Upload multiple quizzes with questions via CSV file</p>
                        </div>
                    </div>
                    <button 
                        onClick={handleClose} 
                        className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-full transition"
                        disabled={isProcessing}
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
                    {/* Template Download Section */}
                    <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                        <div className="flex items-start space-x-3">
                            <FileText size={24} className="text-purple-600 mt-1" />
                            <div>
                                <h3 className="font-semibold text-gray-800 mb-1">Need a template?</h3>
                                <p className="text-sm text-gray-600">
                                    Download our CSV template with sample quizzes and questions to get started quickly.
                                </p>
                                <div className="mt-2 text-xs text-gray-600 space-y-1">
                                    <p>• Group multiple questions by using the same quiz_title</p>
                                    <p>• Question types: multiple_choice or true_false</p>
                                    <p>• For MCQ: provide option_a, option_b (option_c, option_d optional)</p>
                                    <p>• For True/False: correct_answer should be "true" or "false"</p>
                                    <p>• subject_id is optional (leave empty if not needed)</p>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={downloadTemplate}
                            className="w-full md:w-auto justify-center flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition shadow-md whitespace-nowrap"
                        >
                            <Download size={18} className="mr-2" />
                            Download Template
                        </button>
                    </div>

                    {/* File Upload Section */}
                    <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 sm:p-8 text-center hover:border-purple-400 transition">
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileChange}
                            className="hidden"
                            id="csvQuizFileInput"
                            disabled={isProcessing}
                        />
                        <label 
                            htmlFor="csvQuizFileInput" 
                            className={`cursor-pointer ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <Upload size={48} className="mx-auto text-gray-400 mb-4" />
                            <p className="text-lg font-semibold text-gray-700 mb-2">
                                {file ? file.name : 'Click to upload or drag and drop'}
                            </p>
                            <p className="text-sm text-gray-500">
                                CSV files only • Max 50 quizzes per upload
                            </p>
                        </label>
                    </div>

                    {/* Validation Summary */}
                    {validationResults && (
                        <div className={`border-l-4 rounded-lg p-4 ${
                            getSummaryColor() === 'green' ? 'bg-green-50 border-green-500' :
                            getSummaryColor() === 'yellow' ? 'bg-yellow-50 border-yellow-500' :
                            getSummaryColor() === 'red' ? 'bg-red-50 border-red-500' :
                            'bg-gray-50 border-gray-500'
                        }`}>
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="font-bold text-lg text-gray-800 mb-3">Validation Summary</h3>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                                        <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                                            <p className="text-2xl font-bold text-purple-600">{validationResults.uniqueQuizzes}</p>
                                            <p className="text-xs text-gray-600">Unique Quizzes</p>
                                        </div>
                                        <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                                            <p className="text-2xl font-bold text-gray-800">{validationResults.totalRows}</p>
                                            <p className="text-xs text-gray-600">Total Questions</p>
                                        </div>
                                        <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                                            <p className="text-2xl font-bold text-green-600">{validationResults.validCount}</p>
                                            <p className="text-xs text-gray-600">Valid Questions</p>
                                        </div>
                                        <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                                            <p className="text-2xl font-bold text-red-600">{validationResults.errorCount}</p>
                                            <p className="text-xs text-gray-600">Errors</p>
                                        </div>
                                        <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                                            <p className="text-2xl font-bold text-yellow-600">{validationResults.warningCount}</p>
                                            <p className="text-xs text-gray-600">Warnings</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Preview Toggle */}
                    {validationResults && (
                        <button
                            onClick={() => setShowPreview(!showPreview)}
                            className="flex items-center text-purple-600 hover:text-purple-700 font-semibold"
                        >
                            <Eye size={20} className="mr-2" />
                            {showPreview ? 'Hide' : 'Show'} Data Preview & Issues
                        </button>
                    )}

                    {/* Data Preview */}
                    {showPreview && validationResults && (
                        <div className="space-y-4">
                            {/* Quiz Groups Preview */}
                            {Object.entries(validationResults.quizGroups).length > 0 && (
                                <div>
                                    <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                                        <CheckCircle size={20} className="text-green-600 mr-2" />
                                        Quizzes to be Created ({Object.keys(validationResults.quizGroups).length})
                                    </h4>
                                    <div className="space-y-3 max-h-96 overflow-y-auto">
                                        {Object.entries(validationResults.quizGroups).map(([_quizTitle, questions], idx) => (
                                            <div key={idx} className="border-2 border-green-200 rounded-lg p-4 bg-green-50">
                                                <div className="flex justify-between items-start mb-2">
                                                    <h5 className="font-bold text-gray-900">{questions[0].quiz_title}</h5>
                                                    <span className="px-3 py-1 bg-green-600 text-white text-xs rounded-full">
                                                        {questions.length} Questions
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-700 mb-2">{questions[0].quiz_description}</p>
                                                <div className="flex flex-wrap gap-2 text-xs">
                                                    <span className="px-2 py-1 bg-white rounded">⏱️ {questions[0].duration_minutes || 30} mins</span>
                                                    <span className="px-2 py-1 bg-white rounded">✓ {questions[0].marks_per_correct || 1} marks</span>
                                                    <span className="px-2 py-1 bg-white rounded">✗ -{questions[0].negative_marking || 0} marks</span>
                                                    {questions[0].department && (
                                                        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">{questions[0].department}</span>
                                                    )}
                                                    {questions[0].year && (
                                                        <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded">Year {questions[0].year}</span>
                                                    )}
                                                </div>
                                                <div className="mt-3 space-y-2">
                                                    {questions.slice(0, 3).map((q, qIdx) => (
                                                        <div key={qIdx} className="text-sm bg-white p-2 rounded">
                                                            <span className="font-semibold text-gray-700">Q{qIdx + 1}:</span> {q.question_text}
                                                            <span className="ml-2 text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                                                {q.question_type}
                                                            </span>
                                                        </div>
                                                    ))}
                                                    {questions.length > 3 && (
                                                        <p className="text-xs text-gray-500 text-center">... and {questions.length - 3} more questions</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Errors */}
                            {validationResults.errors.length > 0 && (
                                <div>
                                    <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                                        <AlertCircle size={20} className="text-red-600 mr-2" />
                                        Errors ({validationResults.errors.length})
                                    </h4>
                                    <div className="space-y-2 max-h-60 overflow-y-auto">
                                        {validationResults.errors.map((error, idx) => (
                                            <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-3">
                                                <div className="flex justify-between items-start mb-1">
                                                    <p className="font-semibold text-red-800">Row {error.row}</p>
                                                    <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">ERROR</span>
                                                </div>
                                                <p className="text-sm text-gray-700 mb-1">
                                                    {error.data.quiz_title} - {error.data.question_text?.substring(0, 50)}...
                                                </p>
                                                <ul className="list-disc list-inside text-sm text-red-700">
                                                    {error.issues.map((issue, i) => (
                                                        <li key={i}>{issue}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Warnings */}
                            {validationResults.warnings.length > 0 && (
                                <div>
                                    <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                                        <AlertCircle size={20} className="text-yellow-600 mr-2" />
                                        Warnings ({validationResults.warnings.length})
                                    </h4>
                                    <div className="space-y-2 max-h-40 overflow-y-auto">
                                        {validationResults.warnings.map((warning, idx) => (
                                            <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                                <div className="flex justify-between items-start mb-1">
                                                    <p className="font-semibold text-yellow-800">Row {warning.row}</p>
                                                    <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded">WARNING</span>
                                                </div>
                                                <p className="text-sm text-gray-700 mb-1">
                                                    {warning.data.quiz_title} - {warning.data.question_text?.substring(0, 50)}...
                                                </p>
                                                <ul className="list-disc list-inside text-sm text-yellow-700">
                                                    {warning.issues.map((issue, i) => (
                                                        <li key={i}>{issue}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Progress Bar */}
                    {isProcessing && uploadProgress > 0 && (
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Uploading quizzes...</span>
                                <span className="text-gray-600">{uploadProgress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                    className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${uploadProgress}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer Actions */}
                <div className="border-t p-4 sm:p-6 bg-gray-50 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                    <div className="text-sm space-y-1">
                        {canUpload && validationResults && (
                            <p className="flex items-center text-green-600 font-semibold">
                                <CheckCircle size={16} className="mr-1" />
                                Ready to upload {validationResults.uniqueQuizzes} quiz{validationResults.uniqueQuizzes !== 1 ? 'zes' : ''} with {validationResults.validCount} question{validationResults.validCount !== 1 ? 's' : ''}
                            </p>
                        )}
                        {validationResults && validationResults.errorCount > 0 && (
                            <p className="flex items-center text-red-600 font-semibold">
                                <AlertCircle size={16} className="mr-1" />
                                Please fix {validationResults.errorCount} error{validationResults.errorCount !== 1 ? 's' : ''} before uploading
                            </p>
                        )}
                    </div>
                    <div className="w-full sm:w-auto flex flex-col sm:flex-row gap-3 sm:space-x-3">
                        <button
                            onClick={handleClose}
                            disabled={isProcessing}
                            className="w-full sm:w-auto px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleUpload}
                            disabled={!canUpload || isProcessing}
                            className="w-full sm:w-auto justify-center px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition shadow-md disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
                        >
                            {isProcessing ? (
                                <>
                                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Upload size={20} className="mr-2" />
                                    Upload Quizzes
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BulkQuizUploadModal;
