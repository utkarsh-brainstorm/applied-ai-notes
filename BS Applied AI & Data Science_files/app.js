let activeSemesterId = null;
let activeSubjectId = null;
let currentActiveWeek = null;
let curriculumData = (typeof CURRICULUM !== 'undefined') ? CURRICULUM : null;

const semestersList = document.getElementById('semestersList');
const floatingSubpage = document.getElementById('floatingSubpage');
const floatingTabs = document.getElementById('floatingTabs');
const weeksList = document.getElementById('weeksList');
const notesTarget = document.getElementById('notesTarget');
const activeSubjectMeta = document.getElementById('activeSubjectMeta');
const closeBtn = document.getElementById('closeBtn');
const pdfBtn = document.getElementById('pdfBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');

function getCurriculum() {
  return curriculumData || (typeof CURRICULUM !== 'undefined' ? CURRICULUM : { semesters: [] });
}

function getSubjectPrefix(subjectId) {
  const map = {
    'itw': 'IWT',
    'ml2': 'ML2',
    'oop': 'OOP',
    'bdm': 'BDM'
  };
  return map[subjectId] || (subjectId ? subjectId.toUpperCase() : 'SUB');
}

async function init() {
  initTheme();
  renderSemesters();
  bindEvents();
  await loadFreshCurriculum();
}

async function loadFreshCurriculum() {
  try {
    const res = await fetch(`./curriculum.json?_t=${Date.now()}`, { cache: 'no-store' });
    if (res.ok) {
      const freshData = await res.json();
      if (JSON.stringify(freshData) !== JSON.stringify(curriculumData)) {
        curriculumData = freshData;
        renderSemesters();
        if (activeSemesterId && floatingSubpage.classList.contains('active')) {
          const sem = getCurriculum().semesters.find(s => s.id === activeSemesterId);
          if (sem) {
            const subj = sem.subjects.find(s => s.id === activeSubjectId) || sem.subjects[0];
            renderTabs(sem);
            renderSubject(subj);
          }
        }
      }
    }
  } catch (e) {
    // Fallback to static CURRICULUM
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  if (themeToggleBtn) {
    themeToggleBtn.textContent = theme === 'dark' ? 'light' : 'dark';
  }
  const iframe = document.getElementById('activeNoteIframe');
  if (iframe) {
    applyThemeToIframe(iframe);
  }
}

function applyThemeToIframe(iframe) {
  try {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    if (iframe && iframe.contentDocument && iframe.contentDocument.documentElement) {
      iframe.contentDocument.documentElement.setAttribute('data-theme', currentTheme);
    }
  } catch (e) {
    // Cross-origin fallback
  }
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
}

function renderSemesters() {
  semestersList.innerHTML = '';
  const curr = getCurriculum();

  curr.semesters.forEach(sem => {
    const block = document.createElement('div');
    block.className = 'semester-block';
    block.dataset.id = sem.id;

    if (!sem.subjects || sem.subjects.length === 0) {
      block.innerHTML = `
        <button class="sem-btn" aria-expanded="false">
          <span class="sem-title">${sem.title}</span>
          <span class="sem-num">0${sem.id}</span>
        </button>
        <div class="sem-body">
          <div class="empty-sem-container">
            <span class="empty-sem-text">${sem.emptyMessage || 'नहीं है मेरे पास'}</span>
          </div>
        </div>
      `;
    } else {
      block.innerHTML = `
        <button class="sem-btn" aria-expanded="false">
          <span class="sem-title">${sem.title}</span>
          <span class="sem-num">0${sem.id}</span>
        </button>
        <div class="sem-body">
          <div class="subjects-row">
            ${sem.subjects.map(s => `
              <div class="subj-item" data-sem="${sem.id}" data-id="${s.id}">
                <div class="subj-name">${s.name}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    const btn = block.querySelector('.sem-btn');
    btn.addEventListener('click', () => {
      const isOpen = block.classList.contains('open');
      document.querySelectorAll('.semester-block.open').forEach(b => {
        if (b !== block) {
          b.classList.remove('open');
          const otherBtn = b.querySelector('.sem-btn');
          if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
        }
      });
      block.classList.toggle('open', !isOpen);
      btn.setAttribute('aria-expanded', (!isOpen).toString());
    });

    block.querySelectorAll('.subj-item').forEach(card => {
      card.addEventListener('click', (e) => {
        e.stopPropagation();
        openFloatingSubpage(parseInt(card.dataset.sem, 10), card.dataset.id);
      });
    });

    semestersList.appendChild(block);
  });
}

function openFloatingSubpage(semId, subjectId) {
  const sem = getCurriculum().semesters.find(s => s.id === semId);
  if (!sem || !sem.subjects || sem.subjects.length === 0) return;

  activeSemesterId = semId;
  const subj = sem.subjects.find(s => s.id === subjectId) || sem.subjects[0];
  activeSubjectId = subj.id;

  renderTabs(sem);
  renderSubject(subj);

  floatingSubpage.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function renderTabs(sem) {
  floatingTabs.innerHTML = '';
  sem.subjects.forEach(s => {
    const tab = document.createElement('button');
    tab.className = `floating-tab ${s.id === activeSubjectId ? 'active' : ''}`;
    tab.textContent = s.name;
    tab.addEventListener('click', () => {
      if (activeSubjectId === s.id) return;
      activeSubjectId = s.id;
      floatingTabs.querySelectorAll('.floating-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderSubject(s);
    });
    floatingTabs.appendChild(tab);
  });
}

function renderSubject(subj) {
  activeSubjectMeta.textContent = `Sem 0${activeSemesterId} / ${subj.name}`;

  weeksList.innerHTML = '';
  if (subj.weeks && subj.weeks.length > 0) {
    subj.weeks.forEach((w, idx) => {
      const btn = document.createElement('button');
      btn.className = `week-btn ${idx === 0 ? 'active' : ''}`;
      btn.textContent = `Week ${String(w.week).padStart(2, '0')}`;
      btn.addEventListener('click', () => {
        if (currentActiveWeek && currentActiveWeek.week === w.week) return;
        weeksList.querySelectorAll('.week-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderWeekContent(w);
      });
      weeksList.appendChild(btn);
    });

    // Load ONLY the first week initially
    renderWeekContent(subj.weeks[0]);
  } else {
    notesTarget.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted);">No notes available for this subject yet.</div>';
    currentActiveWeek = null;
    updatePdfButton(null);
  }
}

function updatePdfButton(week) {
  if (!pdfBtn) return;
  if (week && week.pdfPath) {
    const prefix = getSubjectPrefix(activeSubjectId);
    const fileName = `${prefix}_Week${week.week}.pdf`;
    pdfBtn.textContent = 'pdf ⤓';
    pdfBtn.title = `Download ${fileName}`;
    pdfBtn.style.display = 'inline-flex';
  } else {
    pdfBtn.style.display = 'none';
  }
}

function renderWeekContent(week) {
  currentActiveWeek = week;
  updatePdfButton(week);

  if (week.htmlPath) {
    const prefix = getSubjectPrefix(activeSubjectId);
    notesTarget.innerHTML = `
      <div class="note-viewer-wrapper">
        <div class="note-loading-indicator" id="noteLoader">
          <div class="loader-spinner"></div>
          <span>Loading ${prefix} Week ${String(week.week).padStart(2, '0')}...</span>
        </div>
        <iframe class="notes-frame" id="activeNoteIframe" src="${week.htmlPath}" title="${week.title || 'Notes'}"></iframe>
      </div>
    `;
    const iframe = document.getElementById('activeNoteIframe');
    const loader = document.getElementById('noteLoader');
    if (iframe) {
      iframe.onload = () => {
        applyThemeToIframe(iframe);
        if (loader) loader.style.display = 'none';
      };
      // Safety timeout to prevent infinite loader
      setTimeout(() => {
        if (loader) loader.style.display = 'none';
      }, 1500);
    }
  } else if (week.content) {
    notesTarget.innerHTML = week.content;
  } else {
    notesTarget.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted);">No content available for this week.</div>';
  }
}

function handleDownloadPdf() {
  if (!currentActiveWeek || !currentActiveWeek.pdfPath) {
    window.print();
    return;
  }
  const prefix = getSubjectPrefix(activeSubjectId);
  const fileName = `${prefix}_Week${currentActiveWeek.week}.pdf`;

  const link = document.createElement('a');
  link.href = currentActiveWeek.pdfPath;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function close() {
  floatingSubpage.classList.remove('active');
  document.body.style.overflow = '';
}

function bindEvents() {
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', toggleTheme);
  }
  closeBtn.addEventListener('click', close);
  if (pdfBtn) {
    pdfBtn.addEventListener('click', handleDownloadPdf);
  }

  floatingSubpage.addEventListener('click', (e) => {
    if (e.target === floatingSubpage) close();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && floatingSubpage.classList.contains('active')) close();
  });
}

document.addEventListener('DOMContentLoaded', init);
