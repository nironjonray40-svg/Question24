
    // State management
    let parsedQuestions = [];
    let selectedFile = null;
    let currentClassId = '';
    let currentSubjectId = '';
    let currentChapterId = '';
    let currentTopicId = '';

    // Elements
    const importClass = document.getElementById('importClass');
    const importSubject = document.getElementById('importSubject');
    const importChapter = document.getElementById('importChapter');
    const importTopic = document.getElementById('importTopic');
    const targetBreadcrumbs = document.getElementById('targetBreadcrumbs');
    const targetReadyBadge = document.getElementById('targetReadyBadge');
    const targetStats = document.getElementById('targetStats');
    const targetQuestionsCount = document.getElementById('targetQuestionsCount');
    const quickAddChapterBtn = document.getElementById('quickAddChapterBtn');
    const quickAddTopicBtn = document.getElementById('quickAddTopicBtn');
    
    const dropzone = document.getElementById('dropzone');
    const dropzonePrompt = document.getElementById('dropzonePrompt');
    const dropzoneLoading = document.getElementById('dropzoneLoading');
    const fileInput = document.getElementById('fileInput');
    const selectedFileInfo = document.getElementById('selectedFileInfo');
    const selectedFileIconWrapper = document.getElementById('selectedFileIconWrapper');
    const selectedFileIcon = document.getElementById('selectedFileIcon');
    const selectedFileName = document.getElementById('selectedFileName');
    const selectedFileSize = document.getElementById('selectedFileSize');
    const removeFileBtn = document.getElementById('removeFileBtn');

    const tabFileUploadBtn = document.getElementById('tabFileUploadBtn');
    const tabTextPasteBtn = document.getElementById('tabTextPasteBtn');
    const tabFileUploadContent = document.getElementById('tabFileUploadContent');
    const tabTextPasteContent = document.getElementById('tabTextPasteContent');
    const rawTextarea = document.getElementById('rawTextarea');
    const parseRawTextBtn = document.getElementById('parseRawTextBtn');
    const insertSampleTextBtn = document.getElementById('insertSampleTextBtn');

    const previewSection = document.getElementById('previewSection');
    const parsedQuestionsList = document.getElementById('parsedQuestionsList');
    const previewTotalBadge = document.getElementById('previewTotalBadge');
    const clearParsedBtn = document.getElementById('clearParsedBtn');
    const executeImportBtn = document.getElementById('executeImportBtn');
    const executeImportBtnText = document.getElementById('executeImportBtnText');
    const bottomTargetLabel = document.getElementById('bottomTargetLabel');

    const existingQuestionsSection = document.getElementById('existingQuestionsSection');
    const existingQuestionsContainer = document.getElementById('existingQuestionsContainer');
    const existingCountBadge = document.getElementById('existingCountBadge');

    // ==========================================
    // CASCADING DROPDOWNS & FILTER MANAGEMENT
    // ==========================================
    // CASCADING DROPDOWNS & DYNAMIC SETTINGS SYNC
    // ==========================================
    
    // Load subjects for a selected class
    async function loadSubjectsForClass(classId, preserveSubjectId = '') {
        if (!classId) {
            currentSubjectId = '';
            currentChapterId = '';
            currentTopicId = '';
            resetDropdown(importSubject, 'প্রথমে শ্রেণি নির্বাচন করুন');
            resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
            resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
            quickAddChapterBtn.classList.add('hidden');
            quickAddTopicBtn.classList.add('hidden');
            return;
        }

        try {
            importSubject.disabled = true;
            importSubject.innerHTML = '<option value="">বিষয় লোড হচ্ছে...</option>';
            const res = await fetch(`/api/subjects/${classId}?t=` + Date.now());
            if (!res.ok) throw new Error('Subjects load failed');
            const subjects = await res.json();

            if (!subjects || subjects.length === 0) {
                importSubject.innerHTML = '<option value="">-- এই শ্রেণিতে কোনো বিষয় নেই --</option>';
                importSubject.disabled = true;
                currentSubjectId = '';
                currentChapterId = '';
                currentTopicId = '';
                resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
                resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
                quickAddChapterBtn.classList.add('hidden');
                quickAddTopicBtn.classList.add('hidden');
                return;
            }

            let sHtml = '<option value="">-- বিষয় নির্বাচন করুন --</option>';
            let subjectStillExists = false;
            subjects.forEach(s => {
                const isSel = String(s.id) === String(preserveSubjectId);
                if (isSel) subjectStillExists = true;
                sHtml += `<option value="${s.id}" ${isSel ? 'selected' : ''}>${escapeHtml(s.name)}</option>`;
            });
            importSubject.innerHTML = sHtml;
            importSubject.disabled = false;
            importSubject.classList.remove('bg-slate-100', 'text-slate-400', 'disabled:cursor-not-allowed');
            importSubject.classList.add('bg-slate-50/70');

            if (preserveSubjectId && subjectStillExists) {
                currentSubjectId = preserveSubjectId;
                importSubject.value = preserveSubjectId;
                quickAddChapterBtn.classList.remove('hidden');
            } else {
                currentSubjectId = '';
                currentChapterId = '';
                currentTopicId = '';
                resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
                resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
                quickAddChapterBtn.classList.add('hidden');
                quickAddTopicBtn.classList.add('hidden');
            }
        } catch (e) {
            console.error('Error loading subjects:', e);
            importSubject.innerHTML = '<option value="">বিষয় লোড করতে ব্যর্থ</option>';
            importSubject.disabled = true;
        }
    }

    // Load chapters for a selected subject
    async function loadChaptersForSubject(subjectId, preserveChapterId = '') {
        if (!subjectId) {
            currentChapterId = '';
            currentTopicId = '';
            resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
            resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
            quickAddTopicBtn.classList.add('hidden');
            return;
        }

        try {
            importChapter.disabled = true;
            importChapter.innerHTML = '<option value="">অধ্যায় লোড হচ্ছে...</option>';
            const res = await fetch(`/api/chapters/${subjectId}?t=` + Date.now());
            if (!res.ok) throw new Error('Chapters load failed');
            const chapters = await res.json();

            if (!chapters || chapters.length === 0) {
                importChapter.innerHTML = '<option value="">-- এই বিষয়ে কোনো অধ্যায় নেই --</option>';
                importChapter.disabled = true;
                currentChapterId = '';
                currentTopicId = '';
                resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
                quickAddTopicBtn.classList.add('hidden');
                return;
            }

            let chHtml = '<option value="">-- অধ্যায় নির্বাচন করুন --</option>';
            let chapterStillExists = false;
            chapters.forEach(ch => {
                const isSel = String(ch.id) === String(preserveChapterId);
                if (isSel) chapterStillExists = true;
                const label = ch.chapter_no ? `${ch.chapter_no}: ${ch.title}` : ch.title;
                chHtml += `<option value="${ch.id}" ${isSel ? 'selected' : ''}>${escapeHtml(label)}</option>`;
            });
            importChapter.innerHTML = chHtml;
            importChapter.disabled = false;
            importChapter.classList.remove('bg-slate-100', 'text-slate-400', 'disabled:cursor-not-allowed');
            importChapter.classList.add('bg-slate-50/70');

            if (preserveChapterId && chapterStillExists) {
                currentChapterId = preserveChapterId;
                importChapter.value = preserveChapterId;
                quickAddTopicBtn.classList.remove('hidden');
            } else {
                currentChapterId = '';
                currentTopicId = '';
                resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
                quickAddTopicBtn.classList.add('hidden');
            }
        } catch (e) {
            console.error('Error loading chapters:', e);
            importChapter.innerHTML = '<option value="">অধ্যায় লোড করতে ব্যর্থ</option>';
            importChapter.disabled = true;
        }
    }

    // Load topics for a selected chapter
    async function loadTopicsForChapter(chapterId, preserveTopicId = '') {
        if (!chapterId) {
            currentTopicId = '';
            resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
            return;
        }

        try {
            importTopic.disabled = true;
            importTopic.innerHTML = '<option value="">টপিক লোড হচ্ছে...</option>';
            const res = await fetch(`/api/topics/${chapterId}?t=` + Date.now());
            if (!res.ok) throw new Error('Topics load failed');
            const topics = await res.json();

            let tHtml = '<option value="">সকল টপিক / সাধারণ অধ্যায় প্রশ্ন</option>';
            let topicStillExists = false;
            if (topics && topics.length > 0) {
                topics.forEach(t => {
                    const isSel = String(t.id) === String(preserveTopicId);
                    if (isSel) topicStillExists = true;
                    tHtml += `<option value="${t.id}" ${isSel ? 'selected' : ''}>${escapeHtml(t.title)}</option>`;
                });
            }
            importTopic.innerHTML = tHtml;
            importTopic.disabled = false;
            importTopic.classList.remove('bg-slate-100', 'text-slate-400', 'disabled:cursor-not-allowed');
            importTopic.classList.add('bg-slate-50/70');

            if (preserveTopicId && topicStillExists) {
                currentTopicId = preserveTopicId;
                importTopic.value = preserveTopicId;
            } else {
                currentTopicId = '';
            }
        } catch (e) {
            console.error('Error loading topics:', e);
            importTopic.innerHTML = '<option value="">টপিক লোড করতে ব্যর্থ</option>';
            importTopic.disabled = true;
        }
    }

    // Continuously sync hierarchy (classes, subjects, chapters, topics) directly from Settings/Database
    let isSyncingHierarchy = false;
    async function syncHierarchyFromSettings(showToast = false) {
        if (isSyncingHierarchy) return;
        isSyncingHierarchy = true;
        const syncIcon = document.getElementById('syncSettingsIcon');
        if (syncIcon) syncIcon.classList.add('fa-spin');

        try {
            const targetClassId = currentClassId || importClass.value;
            const targetSubjectId = currentSubjectId || importSubject.value;
            const targetChapterId = currentChapterId || importChapter.value;
            const targetTopicId = currentTopicId || importTopic.value;

            // 1. Fetch latest classes from settings/database
            const res = await fetch('/api/classes?t=' + Date.now());
            if (!res.ok) throw new Error('Classes fetch failed');
            const classes = await res.json();

            let classExists = false;
            let html = '<option value="">-- শ্রেণি নির্বাচন করুন --</option>';
            classes.forEach(c => {
                const isSel = String(c.id) === String(targetClassId);
                if (isSel) classExists = true;
                html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>${escapeHtml(c.name)}</option>`;
            });
            importClass.innerHTML = html;

            if (targetClassId && classExists) {
                currentClassId = targetClassId;
                importClass.value = targetClassId;

                // 2. Refresh subjects for selected class
                await loadSubjectsForClass(targetClassId, targetSubjectId);

                // 3. Refresh chapters if subject is selected
                if (currentSubjectId) {
                    await loadChaptersForSubject(currentSubjectId, targetChapterId);

                    // 4. Refresh topics if chapter is selected
                    if (currentChapterId) {
                        await loadTopicsForChapter(currentChapterId, targetTopicId);
                    }
                }
            } else {
                currentClassId = '';
                currentSubjectId = '';
                currentChapterId = '';
                currentTopicId = '';
                resetDropdown(importSubject, 'প্রথমে শ্রেণি নির্বাচন করুন');
                resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
                resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
                quickAddChapterBtn.classList.add('hidden');
                quickAddTopicBtn.classList.add('hidden');
            }

            updateTargetStatus();
            fetchExistingQuestions();

            if (showToast && typeof showFastToast === 'function') {
                showFastToast('🔄 সেটিংস থেকে সিলেবাস অপশন সফলভাবে সিঙ্ক হয়েছে!', 'info');
            }
        } catch (e) {
            console.error('Error syncing hierarchy from settings:', e);
            if (showToast) {
                alert('সেটিংস থেকে সিলেবাস আপডেট করতে সমস্যা হয়েছে: ' + e.message);
            }
        } finally {
            isSyncingHierarchy = false;
            if (syncIcon) {
                setTimeout(() => syncIcon.classList.remove('fa-spin'), 350);
            }
        }
    }

    // Manual sync button event
    const syncSettingsBtn = document.getElementById('syncSettingsBtn');
    if (syncSettingsBtn) {
        syncSettingsBtn.addEventListener('click', () => syncHierarchyFromSettings(true));
    }

    // Automatically sync when returning to tab, throttled to prevent dropdown closing
    let lastSyncTime = Date.now();
    window.addEventListener('focus', () => {
        if (Date.now() - lastSyncTime > 4000) {
            lastSyncTime = Date.now();
            syncHierarchyFromSettings(false);
        }
    });
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && Date.now() - lastSyncTime > 4000) {
            lastSyncTime = Date.now();
            syncHierarchyFromSettings(false);
        }
    });

    // 1. Class changed
    importClass.addEventListener('change', async () => {
        currentClassId = importClass.value;
        currentSubjectId = '';
        currentChapterId = '';
        currentTopicId = '';
        
        await loadSubjectsForClass(currentClassId);
        updateTargetStatus();
        fetchExistingQuestions();
    });

    // 2. Subject changed
    importSubject.addEventListener('change', async () => {
        currentSubjectId = importSubject.value;
        currentChapterId = '';
        currentTopicId = '';

        if (!currentSubjectId) {
            quickAddChapterBtn.classList.add('hidden');
            resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
            resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
            quickAddTopicBtn.classList.add('hidden');
            updateTargetStatus();
            fetchExistingQuestions();
            return;
        }

        quickAddChapterBtn.classList.remove('hidden');
        await loadChaptersForSubject(currentSubjectId);
        updateTargetStatus();
        fetchExistingQuestions();
    });

    // 3. Chapter changed
    importChapter.addEventListener('change', async () => {
        currentChapterId = importChapter.value;
        currentTopicId = '';

        if (!currentChapterId) {
            quickAddTopicBtn.classList.add('hidden');
            resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
            updateTargetStatus();
            fetchExistingQuestions();
            return;
        }

        quickAddTopicBtn.classList.remove('hidden');
        await loadTopicsForChapter(currentChapterId);
        updateTargetStatus();
        fetchExistingQuestions();
    });

    // 4. Topic changed
    importTopic.addEventListener('change', () => {
        currentTopicId = importTopic.value;
        updateTargetStatus();
        fetchExistingQuestions();
    });

    // Reset Left Filters button
    document.getElementById('resetLeftFilters').addEventListener('click', () => {
        importClass.value = '';
        currentClassId = '';
        currentSubjectId = '';
        currentChapterId = '';
        currentTopicId = '';
        resetDropdown(importSubject, 'প্রথমে শ্রেণি নির্বাচন করুন');
        resetDropdown(importChapter, 'প্রথমে বিষয় নির্বাচন করুন');
        resetDropdown(importTopic, 'সকল টপিক / সাধারণ অধ্যায় প্রশ্ন');
        quickAddChapterBtn.classList.add('hidden');
        quickAddTopicBtn.classList.add('hidden');
        updateTargetStatus();
        fetchExistingQuestions();
    });

    // Initial silent sync on page ready
    syncHierarchyFromSettings(false);

    function resetDropdown(selectEl, placeholder) {
        selectEl.disabled = true;
        selectEl.innerHTML = `<option value="">${placeholder}</option>`;
        selectEl.classList.remove('bg-slate-50/70');
        selectEl.classList.add('bg-slate-100', 'text-slate-400');
    }

    function updateTargetStatus() {
        const className = importClass.selectedOptions[0]?.text || '';
        const subjectName = importSubject.selectedOptions[0]?.text || '';
        const chapterName = importChapter.selectedOptions[0]?.text || '';
        const topicName = importTopic.selectedOptions[0]?.value ? importTopic.selectedOptions[0]?.text : '';

        const isReady = !!(currentClassId && currentSubjectId && currentChapterId);

        if (isReady) {
            targetReadyBadge.className = 'px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[10px] font-extrabold';
            targetReadyBadge.textContent = 'প্রস্তুত';
            
            let html = `
                <div class="flex items-center gap-1 text-slate-800 font-bold">
                    <i class="fa-solid fa-check-circle text-emerald-600 text-xs"></i>
                    <span>${className}</span>
                </div>
                <div class="pl-4 text-[11px] text-indigo-700 font-semibold">➔ ${subjectName}</div>
                <div class="pl-6 text-[11px] text-amber-800 font-semibold">➔ ${chapterName}</div>
            `;
            if (topicName) {
                html += `<div class="pl-8 text-[11px] text-teal-700 font-semibold">➔ টপিক: ${topicName}</div>`;
            }
            targetBreadcrumbs.innerHTML = html;
            targetStats.classList.remove('hidden');

            bottomTargetLabel.textContent = `${className} > ${subjectName} > ${chapterName}` + (topicName ? ` > ${topicName}` : '');
        } else {
            targetReadyBadge.className = 'px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 text-[10px] font-extrabold';
            targetReadyBadge.textContent = 'অসম্পূর্ণ';
            targetBreadcrumbs.innerHTML = '<div class="text-[11px] text-slate-500 italic">দয়া করে উপরে শ্রেণি, বিষয় ও অধ্যায় নির্বাচন করুন।</div>';
            targetStats.classList.add('hidden');
            bottomTargetLabel.textContent = 'বাম পাশের ফিল্টার অনুযায়ী নির্বাচন করুন';
        }
    }

    async function fetchExistingQuestions() {
        if (!currentClassId || !currentSubjectId || !currentChapterId) {
            existingQuestionsSection.classList.add('hidden');
            return;
        }

        try {
            let url = `/api/questions?class_id=${currentClassId}&subject_id=${currentSubjectId}&chapter_id=${currentChapterId}`;
            if (currentTopicId) {
                url += `&topic_id=${currentTopicId}`;
            }
            const res = await fetch(url);
            const questions = await res.json();
            
            targetQuestionsCount.textContent = `${toBanglaNum(questions.length)}টি`;
            existingCountBadge.textContent = `${toBanglaNum(questions.length)}টি`;

            if (questions.length > 0) {
                existingQuestionsSection.classList.remove('hidden');
                let html = '';
                questions.slice(0, 8).forEach((q, idx) => {
                    const typeLabels = {
                        'mcq': '<span class="px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-[10px] font-bold">MCQ</span>',
                        'cq': '<span class="px-2 py-0.5 rounded bg-teal-50 text-teal-700 text-[10px] font-bold">সৃজনশীল</span>',
                        'short': '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-bold">সংক্ষিপ্ত</span>'
                    };
                    const title = q.mcq_stem || q.cq_stem || q.short_question || 'প্রশ্ন';
                    html += `
                        <div class="p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100/80 border border-slate-200/60 flex items-center justify-between text-xs transition-colors">
                            <div class="flex items-center gap-2 max-w-[85%] truncate">
                                ${typeLabels[q.question_type] || ''}
                                <span class="text-slate-800 truncate font-medium">${escapeHtml(title)}</span>
                            </div>
                            <span class="text-[11px] font-bold text-slate-500">${toBanglaNum(q.marks)} নম্বর</span>
                        </div>
                    `;
                });
                if (questions.length > 8) {
                    html += `<div class="text-center text-[11px] text-brand-600 font-semibold pt-1">আরও ${toBanglaNum(questions.length - 8)}টি প্রশ্ন ডাটাবেজে রয়েছে...</div>`;
                }
                existingQuestionsContainer.innerHTML = html;
            } else {
                existingQuestionsSection.classList.remove('hidden');
                existingQuestionsContainer.innerHTML = `
                    <div class="text-center py-6 text-xs text-slate-400">
                        <i class="fa-solid fa-inbox text-2xl mb-1 text-slate-300"></i>
                        <p>এই অধ্যায়ে এখনও কোনো প্রশ্ন নেই। উপর থেকে ফাইল ইমপোর্ট করে যুক্ত করুন।</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Error fetching existing questions:', e);
        }
    }


    // ==========================================
    // TAB SWITCHING (File Upload vs Text Paste)
    // ==========================================
    tabFileUploadBtn.addEventListener('click', () => {
        tabFileUploadBtn.className = 'px-4 py-2 rounded-xl font-bold text-xs sm:text-sm bg-brand-600 text-white shadow-sm flex items-center gap-2 transition-all';
        tabTextPasteBtn.className = 'px-4 py-2 rounded-xl font-semibold text-xs sm:text-sm bg-slate-100 text-slate-600 hover:bg-slate-200 flex items-center gap-2 transition-all';
        tabFileUploadContent.classList.remove('hidden');
        tabTextPasteContent.classList.add('hidden');
    });

    tabTextPasteBtn.addEventListener('click', () => {
        tabTextPasteBtn.className = 'px-4 py-2 rounded-xl font-bold text-xs sm:text-sm bg-brand-600 text-white shadow-sm flex items-center gap-2 transition-all';
        tabFileUploadBtn.className = 'px-4 py-2 rounded-xl font-semibold text-xs sm:text-sm bg-slate-100 text-slate-600 hover:bg-slate-200 flex items-center gap-2 transition-all';
        tabTextPasteContent.classList.remove('hidden');
        tabFileUploadContent.classList.add('hidden');
    });


    // ==========================================
    // DRAG & DROP FILE HANDLING
    // ==========================================
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dropzone-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        selectedFileInfo.classList.add('hidden');
        if (dropzonePrompt && dropzoneLoading) {
            dropzonePrompt.classList.remove('hidden');
            dropzoneLoading.classList.add('hidden');
        }
        parsedQuestions = [];
        renderPreview();
    });

    async function handleFileSelect(file) {
        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
        selectedFileInfo.classList.remove('hidden');

        const fname = file.name.toLowerCase();

        // Update badge icon based on file type
        if (fname.endsWith('.pdf')) {
            if (selectedFileIconWrapper) {
                selectedFileIconWrapper.className = 'w-9 h-9 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold';
            }
            if (selectedFileIcon) {
                selectedFileIcon.className = 'fa-solid fa-file-pdf';
            }
            await parsePdfFile(file);
            return;
        } else {
            if (selectedFileIconWrapper) {
                selectedFileIconWrapper.className = 'w-9 h-9 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold';
            }
            if (selectedFileIcon) {
                selectedFileIcon.className = 'fa-solid fa-file-code';
            }
        }

        const reader = new FileReader();

        reader.onload = function(evt) {
            const content = evt.target.result;
            if (fname.endsWith('.json')) {
                parseJsonContent(content);
            } else if (fname.endsWith('.csv') || fname.endsWith('.tsv')) {
                parseCsvContent(content, fname.endsWith('.tsv') ? '\t' : ',');
            } else {
                parseTextContent(content);
            }
        };

        reader.readAsText(file, 'UTF-8');
    }

    async function parsePdfFile(file) {
        if (dropzonePrompt && dropzoneLoading) {
            dropzonePrompt.classList.add('hidden');
            dropzoneLoading.classList.remove('hidden');
        }

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/parse-pdf', {
                method: 'POST',
                body: formData
            });

            const result = await res.json();

            if (result.success) {
                if (result.questions && result.questions.length > 0) {
                    parsedQuestions = result.questions.map(item => normalizeQuestionObject(item));
                    if (rawTextarea) rawTextarea.value = result.raw_text || '';
                    renderPreview();
                    if (typeof showFastToast === 'function') {
                        showFastToast(`📄 PDF থেকে মোট ${toBanglaNum(result.questions.length)}টি প্রশ্ন প্রস্তুত হয়েছে!`, 'success');
                    }
                } else {
                    if (rawTextarea) rawTextarea.value = result.raw_text || '';
                    alert(result.message || 'PDF থেকে টেক্সট পাওয়া গেছে, কিন্তু কোনো প্রশ্ন ফরম্যাটে মেলেনি। "সরাসরি টেক্সট পেস্ট" ট্যাবে টেক্সট এডিট করে নিতে পারেন।');
                    if (tabTextPasteBtn) tabTextPasteBtn.click();
                }
            } else {
                alert('ত্রুটি: ' + (result.message || 'PDF ফাইল পার্স করা সম্ভব হয়নি।'));
                if (result.raw_text && rawTextarea) {
                    rawTextarea.value = result.raw_text;
                    if (tabTextPasteBtn) tabTextPasteBtn.click();
                }
            }
        } catch (err) {
            console.error('PDF parsing error:', err);
            alert('সার্ভারের সাথে যোগাযোগ করতে সমস্যা হয়েছে: ' + err.message);
        } finally {
            if (dropzonePrompt && dropzoneLoading) {
                dropzonePrompt.classList.remove('hidden');
                dropzoneLoading.classList.add('hidden');
            }
        }
    }


    // ==========================================
    // PARSERS (JSON, CSV, Structured Text)
    // ==========================================
    function parseJsonContent(text) {
        try {
            const data = JSON.parse(text);
            const rawList = Array.isArray(data) ? data : (data.questions || []);
            parsedQuestions = rawList.map(item => normalizeQuestionObject(item));
            renderPreview();
        } catch (e) {
            alert('JSON ফাইলটি সঠিকভাবে পড়তে পারা যায়নি। ফরম্যাট যাচাই করুন: ' + e.message);
        }
    }

    function parseCsvContent(text, delimiter = ',') {
        try {
            const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter(l => l.trim().length > 0);
            if (lines.length < 2) {
                alert('CSV ফাইলে পর্যাপ্ত ডাটা পাওয়া যায়নি।');
                return;
            }
            
            // Basic CSV header & row parser
            const parseRow = (rowStr) => {
                const result = [];
                let current = '';
                let inQuotes = false;
                for (let i = 0; i < rowStr.length; i++) {
                    const char = rowStr[i];
                    if (char === '"' || char === "'") {
                        inQuotes = !inQuotes;
                    } else if (char === delimiter && !inQuotes) {
                        result.push(current.trim());
                        current = '';
                    } else {
                        current += char;
                    }
                }
                result.push(current.trim());
                return result;
            };

            const headers = parseRow(lines[0]).map(h => h.toLowerCase().replace(/['"]/g, '').trim());
            const list = [];

            for (let i = 1; i < lines.length; i++) {
                const cols = parseRow(lines[i]).map(c => c.replace(/^["']|["']$/g, '').trim());
                if (cols.length === 0 || cols.every(c => !c)) continue;
                
                const obj = {};
                headers.forEach((h, idx) => {
                    obj[h] = cols[idx] || '';
                });
                list.push(normalizeQuestionObject(obj));
            }

            parsedQuestions = list;
            renderPreview();
        } catch (e) {
            alert('CSV ফাইল পার্স করতে সমস্যা হয়েছে: ' + e.message);
        }
    }

    function parseTextContent(text) {
        // Try JSON first
        try {
            const data = JSON.parse(text);
            const rawList = Array.isArray(data) ? data : (data.questions || []);
            parsedQuestions = rawList.map(item => normalizeQuestionObject(item));
            renderPreview();
            return;
        } catch (e) {
            // Not JSON, continue to text parsing
        }

        const blocks = text.replace(/\r\n/g, '\n').split(/\n\s*\n\s*\n/).filter(b => b.trim().length > 0);
        const actualBlocks = blocks.length > 1 ? blocks : text.split(/\n(?=\[[^\]]+\]|\n---|\n===)/);

        const list = [];
        actualBlocks.forEach(block => {
            const lines = block.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            if (lines.length === 0) return;

            const blockStr = lines.join('\n');

            if (blockStr.includes('উদ্দীপক') || blockStr.includes('দৃশ্যকল্প') || (blockStr.includes('ক)') && blockStr.includes('খ)'))) {
                let stem = '', ka = '', kha = '', ga = '', gha = '', sol = '';
                let cur = 'stem';

                lines.forEach(line => {
                    if (line.startsWith('উদ্দীপক:') || line.startsWith('দৃশ্যকল্প:')) {
                        cur = 'stem';
                        stem += line.substring(line.indexOf(':') + 1).trim() + '\n';
                    } else if (line.startsWith('ক)') || line.startsWith('ক.') || line.startsWith('ক:')) {
                        cur = 'ka';
                        ka = line.replace(/^[ক\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('খ)') || line.startsWith('খ.') || line.startsWith('খ:')) {
                        cur = 'kha';
                        kha = line.replace(/^[খ\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('গ)') || line.startsWith('গ.') || line.startsWith('গ:')) {
                        cur = 'ga';
                        ga = line.replace(/^[গ\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('ঘ)') || line.startsWith('ঘ.') || line.startsWith('ঘ:')) {
                        cur = 'gha';
                        gha = line.replace(/^[ঘ\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('সমাধান:') || line.startsWith('উত্তর:')) {
                        cur = 'sol';
                        sol += line.substring(line.indexOf(':') + 1).trim() + '\n';
                    } else if (line.startsWith('[')) {
                        // ignore header
                    } else {
                        if (cur === 'stem') stem += line + '\n';
                        else if (cur === 'ka') ka += ' ' + line;
                        else if (cur === 'kha') kha += ' ' + line;
                        else if (cur === 'ga') ga += ' ' + line;
                        else if (cur === 'gha') gha += ' ' + line;
                        else if (cur === 'sol') sol += line + '\n';
                    }
                });

                list.push({
                    question_type: 'cq',
                    difficulty: 'medium',
                    marks: 10.0,
                    cq_stem: stem.trim(),
                    cq_sub_ka: ka.trim(),
                    cq_sub_kha: kha.trim(),
                    cq_sub_ga: ga.trim(),
                    cq_sub_gha: gha.trim(),
                    cq_solution: sol.trim()
                });
            } else if (blockStr.includes('ক)') || blockStr.includes('খ)') || blockStr.includes('A)') || blockStr.includes('B)')) {
                // MCQ
                let q_stem = '', opt_a = '', opt_b = '', opt_c = '', opt_d = '', ans = '', exp = '';
                lines.forEach(line => {
                    if (line.startsWith('প্রশ্ন:') || line.startsWith('Q:')) {
                        q_stem = line.substring(line.indexOf(':') + 1).trim();
                    } else if (line.startsWith('ক)') || line.startsWith('ক.') || line.startsWith('A)') || line.startsWith('A.')) {
                        opt_a = line.replace(/^[কA\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('খ)') || line.startsWith('খ.') || line.startsWith('B)') || line.startsWith('B.')) {
                        opt_b = line.replace(/^[খB\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('গ)') || line.startsWith('গ.') || line.startsWith('C)') || line.startsWith('C.')) {
                        opt_c = line.replace(/^[গC\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('ঘ)') || line.startsWith('ঘ.') || line.startsWith('D)') || line.startsWith('D.')) {
                        opt_d = line.replace(/^[ঘD\)\.\:\s]+/, '').trim();
                    } else if (line.startsWith('সঠিক উত্তর:') || line.startsWith('উত্তর:') || line.startsWith('Ans:')) {
                        ans = line.substring(line.indexOf(':') + 1).trim();
                    } else if (line.startsWith('ব্যাখ্যা:') || line.startsWith('Exp:')) {
                        exp = line.substring(line.indexOf(':') + 1).trim();
                    } else if (!q_stem && !line.startsWith('[')) {
                        q_stem = line;
                    }
                });

                list.push({
                    question_type: 'mcq',
                    difficulty: 'medium',
                    marks: 1.0,
                    mcq_stem: q_stem.trim(),
                    option_a: opt_a.trim(),
                    option_b: opt_b.trim(),
                    option_c: opt_c.trim(),
                    option_d: opt_d.trim(),
                    correct_option: ans.trim(),
                    explanation: exp.trim()
                });
            } else {
                // Short
                let q_text = '', a_text = '';
                lines.forEach(line => {
                    if (line.startsWith('প্রশ্ন:') || line.startsWith('Q:')) {
                        q_text = line.substring(line.indexOf(':') + 1).trim();
                    } else if (line.startsWith('উত্তর:') || line.startsWith('Ans:') || line.startsWith('সমাধান:')) {
                        a_text = line.substring(line.indexOf(':') + 1).trim();
                    } else if (!q_text && !line.startsWith('[')) {
                        q_text = line;
                    } else if (q_text && !a_text) {
                        a_text = line;
                    }
                });

                if (q_text) {
                    list.push({
                        question_type: 'short',
                        difficulty: 'medium',
                        marks: 2.0,
                        short_question: q_text.trim(),
                        short_answer: a_text.trim()
                    });
                }
            }
        });

        parsedQuestions = list;
        renderPreview();
    }

    function normalizeQuestionObject(item) {
        let type = (item.question_type || item.type || item.ধরন || '').toString().toLowerCase().trim();
        if (['cq', 'creative', 'সৃজনশীল', 'গঠনমূলক', 'structured'].includes(type)) {
            type = 'cq';
        } else if (['mcq', 'multiple_choice', 'বহুনির্বাচনি', 'নৈর্ব্যক্তিক'].includes(type)) {
            type = 'mcq';
        } else if (['short', 'সংক্ষিপ্ত'].includes(type)) {
            type = 'short';
        } else {
            if (item.cq_stem || item.sub_ka || item.উদ্দীপক || item.ক) type = 'cq';
            else if (item.option_a || item.opt_a || item['ক)']) type = 'mcq';
            else type = 'short';
        }

        const difficulty = ['easy', 'सहज', 'সহজ'].includes(item.difficulty) ? 'easy' : (['hard', 'কঠিন'].includes(item.difficulty) ? 'hard' : 'medium');
        const marks = parseFloat(item.marks || (type === 'cq' ? 10.0 : (type === 'short' ? 2.0 : 1.0))) || 1.0;

        const obj = {
            question_type: type,
            difficulty: difficulty,
            marks: marks,
            topic_title: item.topic_title || item.topic || item.টপিক || ''
        };

        if (type === 'cq') {
            obj.cq_stem = item.cq_stem || item.stem || item.উদ্দীপক || item.দৃশ্যকল্প || '';
            obj.cq_sub_ka = item.cq_sub_ka || item.sub_ka || item.ka || item.ক || item['ক)'] || '';
            obj.cq_sub_kha = item.cq_sub_kha || item.sub_kha || item.kha || item.খ || item['খ)'] || '';
            obj.cq_sub_ga = item.cq_sub_ga || item.sub_ga || item.ga || item.গ || item['গ)'] || '';
            obj.cq_sub_gha = item.cq_sub_gha || item.sub_gha || item.gha || item.ঘ || item['ঘ)'] || '';
            obj.cq_solution = item.cq_solution || item.solution || item.সমাধান || item.উত্তর || '';
        } else if (type === 'mcq') {
            obj.mcq_stem = item.mcq_stem || item.question || item.stem || item.প্রশ্ন || '';
            obj.option_a = item.option_a || item.opt_a || item.a || item.ক || '';
            obj.option_b = item.option_b || item.opt_b || item.b || item.খ || '';
            obj.option_c = item.option_c || item.opt_c || item.c || item.গ || '';
            obj.option_d = item.option_d || item.opt_d || item.d || item.ঘ || '';
            obj.correct_option = item.correct_option || item.answer || item.correct_ans || item.সঠিক_উত্তর || '';
            obj.explanation = item.explanation || item.ব্যাখ্যা || '';
        } else {
            obj.short_question = item.short_question || item.question || item.প্রশ্ন || '';
            obj.short_answer = item.short_answer || item.answer || item.উত্তর || '';
        }

        return obj;
    }


    // ==========================================
    // PARSE DIRECT TEXT BUTTON & DEMO BUTTON
    // ==========================================
    parseRawTextBtn.addEventListener('click', () => {
        const text = rawTextarea.value.trim();
        if (!text) {
            alert('অনুগ্রহ করে টেক্সট বক্সে প্রশ্ন পেস্ট করুন।');
            return;
        }
        parseTextContent(text);
    });

    insertSampleTextBtn.addEventListener('click', () => {
        rawTextarea.value = `[সৃজনশীল ১]
উদ্দীপক: দশম শ্রেণির ছাত্রী মিতু চোখে দেখে না। কিন্তু তার স্মৃতিশক্তি প্রখর এবং গানের গলা চমৎকার। পরিবারের সদস্যরা তাকে নিয়ে লজ্জিত না হয়ে তার সংগীত চর্চায় সর্বাত্মক সহায়তা করেন। ফলে মিতু জাতীয় পর্যায়ে শ্রেষ্ঠ সংগীতশিল্পী হিসেবে পুরস্কার অর্জন করে।
ক) সুভার পিতার নাম কী?
খ) ‘সুভার একটি বিশেষ সুবিধা ছিল’—কথাটি দ্বারা কী বোঝানো হয়েছে?
গ) উদ্দীপকের মিতুর পারিবারিক পরিবেশ ‘সুভা’ গল্পের কোন ভিন্ন দিকটি উন্মোচন করে? ব্যাখ্যা কর।
ঘ) “মিতু অনুকূল পরিবেশ পেলেও সুভা তা থেকে বঞ্চিত ছিল”—মন্তব্যটি ‘সুভা’ গল্পের আলোকে বিশ্লেষণ কর।
সমাধান: ক) বাণীকণ্ঠ। খ) বাকপ্রতিবন্ধী হওয়ায় সাধারণ মানুষের চেয়ে প্রকৃতির সাথে নিবিড় সখ্য।

[বহুনির্বাচনি ১]
প্রশ্ন: সুভার সাথে কার ঘনিষ্ঠ বন্ধুত্ব ছিল?
ক) প্রতাপ
খ) গোঁসাইদের ছোট ছেলে
গ) সর্বশী ও পাঙ্গুলি নামের দুটি গাভী
ঘ) গ্রামের সমবয়সী মেয়েরা
সঠিক উত্তর: গ
ব্যাখ্যা: সুভার মূক প্রকৃতির সাথে বোবা প্রাণী দুটি অন্তরঙ্গ বন্ধু ছিল।

[সংক্ষিপ্ত ১]
প্রশ্ন: সুভার মা কেন সুভাকে নিজের গর্ভের কলঙ্ক মনে করতেন?
উত্তর: সাধারণত মায়েরা মেয়ের মধ্যে নিজের প্রতিচ্ছবি দেখতে চান। সুভা জন্মগতভাবে বাকপ্রতিবন্ধী হওয়ায় মা তাকে নিজের ত্রুটি ও দুর্ভাগ্যের প্রতীক তথা গর্ভের কলঙ্ক মনে করতেন।`;
    });


    // ==========================================
    // RENDER LIVE PREVIEW
    // ==========================================
    function renderPreview() {
        if (!parsedQuestions || parsedQuestions.length === 0) {
            previewSection.classList.add('hidden');
            return;
        }

        previewSection.classList.remove('hidden');
        previewTotalBadge.textContent = `মোট: ${toBanglaNum(parsedQuestions.length)}টি`;

        let html = '';
        parsedQuestions.forEach((q, idx) => {
            const isCQ = q.question_type === 'cq';
            const isMCQ = q.question_type === 'mcq';
            const isShort = q.question_type === 'short';

            let typeBadge = '';
            if (isCQ) typeBadge = '<span class="px-2.5 py-0.5 rounded-md bg-teal-100 text-teal-800 font-extrabold text-[11px]"><i class="fa-solid fa-shapes mr-1"></i> সৃজনশীল/গঠনমূলক</span>';
            else if (isMCQ) typeBadge = '<span class="px-2.5 py-0.5 rounded-md bg-purple-100 text-purple-800 font-extrabold text-[11px]"><i class="fa-solid fa-list-check mr-1"></i> বহুনির্বাচনি (MCQ)</span>';
            else typeBadge = '<span class="px-2.5 py-0.5 rounded-md bg-amber-100 text-amber-800 font-extrabold text-[11px]"><i class="fa-solid fa-align-left mr-1"></i> সংক্ষিপ্ত প্রশ্ন</span>';

            html += `
                <div class="p-4 sm:p-5 rounded-2xl bg-slate-50/70 border border-slate-200/90 space-y-3 relative group hover:border-brand-400 transition-colors">
                    <div class="flex items-center justify-between border-b border-slate-200/60 pb-2.5">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center">${toBanglaNum(idx + 1)}</span>
                            ${typeBadge}
                            ${q.topic_title ? `<span class="px-2 py-0.5 rounded-md bg-slate-200/80 text-slate-700 text-[10px] font-semibold"><i class="fa-solid fa-tag text-teal-600 mr-0.5"></i> ${escapeHtml(q.topic_title)}</span>` : ''}
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="text-xs font-bold text-slate-500">${toBanglaNum(q.marks)} নম্বর</span>
                            <button type="button" onclick="removeSingleQuestion(${idx})" class="text-slate-400 hover:text-rose-600 p-1 text-sm transition-colors" title="মুছে ফেলুন">
                                <i class="fa-solid fa-xmark"></i>
                            </button>
                        </div>
                    </div>

                    <div class="space-y-2.5 text-xs text-slate-800 font-tiro">
            `;

            if (isCQ) {
                html += `
                    <div class="p-3 rounded-xl bg-white border border-slate-200 font-tiro leading-relaxed text-slate-900 shadow-sm text-sm">
                        <strong class="text-brand-700 font-bangla text-xs block mb-1">দৃশ্যকল্প / উদ্দীপক:</strong>
                        ${escapeHtml(q.cq_stem || '(কোনো উদ্দীপক দেওয়া হয়নি)')}
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm font-tiro">
                        <div class="p-2.5 rounded-lg bg-white border border-slate-200"><strong class="text-slate-600 font-bangla">ক)</strong> ${escapeHtml(q.cq_sub_ka || '')} <span class="text-[10px] text-slate-400 font-bold float-right font-bangla">[১]</span></div>
                        <div class="p-2.5 rounded-lg bg-white border border-slate-200"><strong class="text-slate-600 font-bangla">খ)</strong> ${escapeHtml(q.cq_sub_kha || '')} <span class="text-[10px] text-slate-400 font-bold float-right font-bangla">[২]</span></div>
                        <div class="p-2.5 rounded-lg bg-white border border-slate-200"><strong class="text-slate-600 font-bangla">গ)</strong> ${escapeHtml(q.cq_sub_ga || '')} <span class="text-[10px] text-slate-400 font-bold float-right font-bangla">[৩]</span></div>
                        <div class="p-2.5 rounded-lg bg-white border border-slate-200"><strong class="text-slate-600 font-bangla">ঘ)</strong> ${escapeHtml(q.cq_sub_gha || '')} <span class="text-[10px] text-slate-400 font-bold float-right font-bangla">[৪]</span></div>
                    </div>
                `;
                if (q.cq_solution) {
                    html += `<div class="text-xs font-tiro text-emerald-800 bg-emerald-50/80 p-2.5 rounded-lg border border-emerald-200/60"><strong class="text-emerald-900 font-bangla">সমাধান / নির্দেশনা:</strong> ${escapeHtml(q.cq_solution)}</div>`;
                }
            } else if (isMCQ) {
                html += `
                    <div class="font-bold text-slate-900 text-sm font-tiro leading-relaxed">
                        ${escapeHtml(q.mcq_stem || '')}
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-sm font-tiro">
                        <div class="p-2 rounded-lg bg-white border ${['a', 'ক', '1'].includes(String(q.correct_option).toLowerCase()) ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-900' : 'border-slate-200'}">
                            <span class="text-slate-400 mr-1 font-bangla">ক)</span> ${escapeHtml(q.option_a || '')}
                        </div>
                        <div class="p-2 rounded-lg bg-white border ${['b', 'খ', '2'].includes(String(q.correct_option).toLowerCase()) ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-900' : 'border-slate-200'}">
                            <span class="text-slate-400 mr-1 font-bangla">খ)</span> ${escapeHtml(q.option_b || '')}
                        </div>
                        <div class="p-2 rounded-lg bg-white border ${['c', 'গ', '3'].includes(String(q.correct_option).toLowerCase()) ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-900' : 'border-slate-200'}">
                            <span class="text-slate-400 mr-1 font-bangla">গ)</span> ${escapeHtml(q.option_c || '')}
                        </div>
                        <div class="p-2 rounded-lg bg-white border ${['d', 'ঘ', '4'].includes(String(q.correct_option).toLowerCase()) ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-900' : 'border-slate-200'}">
                            <span class="text-slate-400 mr-1 font-bangla">ঘ)</span> ${escapeHtml(q.option_d || '')}
                        </div>
                    </div>
                `;
                if (q.explanation) {
                    html += `<div class="text-xs font-tiro text-purple-800 bg-purple-50/70 p-2 rounded-lg border border-purple-200/50"><strong class="text-purple-900 font-bangla">ব্যাখ্যা:</strong> ${escapeHtml(q.explanation)}</div>`;
                }
            } else {
                html += `
                    <div class="font-bold text-slate-900 text-sm font-tiro leading-relaxed">
                        ${escapeHtml(q.short_question || '')}
                    </div>
                    <div class="p-2.5 rounded-lg bg-white border border-slate-200 text-xs font-tiro text-slate-700">
                        <strong class="text-amber-800 block mb-0.5 font-bangla">মডেল উত্তর:</strong>
                        ${escapeHtml(q.short_answer || '(কোনো উত্তর উল্লেখ নেই)')}
                    </div>
                `;
            }

            html += `
                    </div>
                </div>
            `;
        });

        parsedQuestionsList.innerHTML = html;
        executeImportBtnText.textContent = `ডাটাবেজে ইমপোর্ট সম্পন্ন করুন (${toBanglaNum(parsedQuestions.length)}টি প্রশ্ন)`;
    }

    window.removeSingleQuestion = function(index) {
        parsedQuestions.splice(index, 1);
        renderPreview();
    };

    clearParsedBtn.addEventListener('click', async () => {
        const confirmed = await showConfirmDialog({
            title: 'সকল প্রশ্ন মুছে ফেলা',
            message: 'আপনি কি প্রিভিউতে থাকা সকল প্রশ্ন মুছে ফেলতে চান?',
            confirmText: 'হ্যাঁ, সব মুছুন',
            cancelText: 'বাতিল করুন',
            type: 'danger'
        });
        if (confirmed) {
            parsedQuestions = [];
            renderPreview();
        }
    });


    // ==========================================
    // EXECUTE IMPORT TO DATABASE
    // ==========================================
    executeImportBtn.addEventListener('click', async () => {
        if (!currentClassId || !currentSubjectId || !currentChapterId) {
            alert('দয়া করে পর্দার বাম পাশ থেকে ক্লাসের নাম, বিষয়ের নাম এবং অধ্যায় নির্বাচন করুন।');
            importClass.focus();
            return;
        }

        if (!parsedQuestions || parsedQuestions.length === 0) {
            alert('ইমপোর্ট করার জন্য কোনো প্রশ্ন পাওয়া যায়নি। দয়া করে ফাইল আপলোড বা টেক্সট পেস্ট করুন।');
            return;
        }

        try {
            executeImportBtn.disabled = true;
            executeImportBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-base"></i><span>ইমপোর্ট হচ্ছে...</span>';

            const payload = {
                class_id: parseInt(currentClassId),
                subject_id: parseInt(currentSubjectId),
                chapter_id: parseInt(currentChapterId),
                topic_id: currentTopicId ? parseInt(currentTopicId) : null,
                questions: parsedQuestions
            };

            const res = await fetch('/api/v1/fast-save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await res.json();

            if (result.success) {
                const speedText = result.time_taken_ms ? ` (মাত্র ${result.time_taken_ms} মিলিসেকেন্ডে!)` : '';
                document.getElementById('successMessage').textContent = (result.message || 'প্রশ্নগুলো সফলভাবে ডাটাবেজে সংরক্ষণ করা হয়েছে।') + speedText;
                document.getElementById('successModal').classList.remove('hidden');
                
                if (typeof showFastToast === 'function') {
                    showFastToast(`⚡ ${toBanglaNum(result.count || parsedQuestions.length)}টি প্রশ্ন মাত্র ${result.time_taken_ms || 3} ms এ সংরক্ষিত হয়েছে!`, 'success');
                }

                // Clear state
                parsedQuestions = [];
                selectedFile = null;
                fileInput.value = '';
                rawTextarea.value = '';
                selectedFileInfo.classList.add('hidden');
                renderPreview();
                fetchExistingQuestions();
            } else {
                alert('ত্রুটি: ' + (result.message || 'ইমপোর্ট করা সম্ভব হয়নি।'));
            }
        } catch (e) {
            console.error('Import error:', e);
            alert('সার্ভারে যোগাযোগ করতে সমস্যা হয়েছে: ' + e.message);
        } finally {
            executeImportBtn.disabled = false;
            executeImportBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up text-base"></i><span>ডাটাবেজে ইমপোর্ট সম্পন্ন করুন</span>';
        }
    });

    window.closeSuccessModal = function() {
        document.getElementById('successModal').classList.add('hidden');
    };


    // ==========================================
    // QUICK ADD MODAL (Chapter / Topic)
    // ==========================================
    quickAddChapterBtn.addEventListener('click', () => {
        document.getElementById('quickAddType').value = 'chapter';
        document.getElementById('quickAddModalTitle').innerHTML = '<i class="fa-solid fa-folder-plus text-amber-600"></i> নতুন অধ্যায় যোগ করুন';
        document.getElementById('quickAddChapterNoGroup').classList.remove('hidden');
        document.getElementById('quickAddTitleLabel').innerHTML = 'অধ্যায়ের নাম / শিরোনাম <span class="text-rose-500">*</span>';
        document.getElementById('quickAddTitle').placeholder = 'যেমন: বাস্তব সংখ্যা, বল ও গতি...';
        document.getElementById('quickAddTitle').value = '';
        document.getElementById('quickAddChapterNo').value = '';
        document.getElementById('quickAddModal').classList.remove('hidden');
    });

    quickAddTopicBtn.addEventListener('click', () => {
        document.getElementById('quickAddType').value = 'topic';
        document.getElementById('quickAddModalTitle').innerHTML = '<i class="fa-solid fa-tag text-teal-600"></i> নতুন টপিক / পাঠ যোগ করুন';
        document.getElementById('quickAddChapterNoGroup').classList.add('hidden');
        document.getElementById('quickAddTitleLabel').innerHTML = 'টপিক / পাঠের শিরোনাম <span class="text-rose-500">*</span>';
        document.getElementById('quickAddTitle').placeholder = 'যেমন: পাঠ ১: মূলদ ও অমূলদ সংখ্যা...';
        document.getElementById('quickAddTitle').value = '';
        document.getElementById('quickAddModal').classList.remove('hidden');
    });

    window.closeQuickAddModal = function() {
        document.getElementById('quickAddModal').classList.add('hidden');
    };

    document.getElementById('quickAddForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const type = document.getElementById('quickAddType').value;
        const title = document.getElementById('quickAddTitle').value.trim();
        const chapterNo = document.getElementById('quickAddChapterNo').value.trim();

        if (!title) return;

        try {
            if (type === 'chapter') {
                const res = await fetch('/api/chapters/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        subject_id: parseInt(currentSubjectId),
                        title: title,
                        chapter_no: chapterNo
                    })
                });
                const newCh = await res.json();
                
                // Add to dropdown and auto-select
                const label = newCh.chapter_no ? `${newCh.chapter_no}: ${newCh.title}` : newCh.title;
                const opt = new Option(label, newCh.id, true, true);
                importChapter.add(opt);
                importChapter.value = newCh.id;
                currentChapterId = newCh.id;
                importChapter.dispatchEvent(new Event('change'));
            } else {
                const res = await fetch('/api/topics/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        chapter_id: parseInt(currentChapterId),
                        title: title
                    })
                });
                const newT = await res.json();
                
                // Add to dropdown and auto-select
                const opt = new Option(newT.title, newT.id, true, true);
                importTopic.add(opt);
                importTopic.value = newT.id;
                currentTopicId = newT.id;
                importTopic.dispatchEvent(new Event('change'));
            }
            closeQuickAddModal();
        } catch (err) {
            console.error('Error creating hierarchy item:', err);
            alert('তৈরি করতে ব্যর্থ হয়েছে: ' + err.message);
        }
    });


    // ==========================================
    // UTILITY HELPERS
    // ==========================================
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .replace(/\n/g, '<br>');
    }

