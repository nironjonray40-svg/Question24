// Mock DOM environment for Node.js
class MockElement {
    constructor(id) {
        this.id = id;
        this.value = '';
        this.innerHTML = '';
        this.disabled = false;
        this.classList = {
            classes: new Set(),
            add: (...cls) => cls.forEach(c => this.classList.classes.add(c)),
            remove: (...cls) => cls.forEach(c => this.classList.classes.delete(c)),
            contains: (c) => this.classList.classes.has(c)
        };
        this.listeners = {};
        this.selectedOptions = [{ text: '', value: '' }];
    }

    addEventListener(evt, cb) {
        if (!this.listeners[evt]) this.listeners[evt] = [];
        this.listeners[evt].push(cb);
    }

    dispatchEvent(evt) {
        const type = typeof evt === 'string' ? evt : evt.type;
        if (this.listeners[type]) {
            this.listeners[type].forEach(cb => cb());
        }
    }

    focus() {}
}

const elements = {};
const getEl = (id) => {
    if (!elements[id]) elements[id] = new MockElement(id);
    return elements[id];
};

global.document = {
    getElementById: (id) => getEl(id),
    addEventListener: () => {},
    visibilityState: 'visible'
};
global.window = {
    addEventListener: () => {}
};
global.Event = class { constructor(type) { this.type = type; } };
global.Option = class { constructor(text, val) { this.text = text; this.value = val; } };

// Mock real fetch to http://127.0.0.1:5000
const originalFetch = global.fetch;
global.fetch = async (url, opts) => {
    if (url.startsWith('/')) {
        url = 'http://127.0.0.1:5000' + url;
    }
    return originalFetch(url, opts);
};

// Now load and run script_0.js
const fs = require('fs');
let code = fs.readFileSync('scratch/script_0.js', 'utf-8');

// Execute script
eval(code);

async function testCascade() {
    console.log('Testing cascading selection...');
    const importClass = getEl('importClass');
    const importSubject = getEl('importSubject');
    const importChapter = getEl('importChapter');
    const importTopic = getEl('importTopic');

    // 1. User selects Class 3 (৮ম শ্রেণি)
    console.log('\nStep 1: Selecting Class 3 (৮ম শ্রেণি)');
    importClass.value = '3';
    await importClass.listeners['change'][0]();

    console.log('importSubject.disabled =', importSubject.disabled);
    console.log('importSubject options sample =', importSubject.innerHTML.substring(0, 150));
    if (importSubject.disabled === false && importSubject.innerHTML.includes('বাংলা')) {
        console.log('✓ Class 3 successfully UNLOCKED subjects and populated বাংলা!');
    } else {
        console.error('✗ Subject failed to unlock!');
        process.exit(1);
    }

    // 2. User selects Subject 47 (বাংলা ১ম পত্র)
    console.log('\nStep 2: Selecting Subject 47 (বাংলা ১ম পত্র)');
    importSubject.value = '47';
    await importSubject.listeners['change'][0]();

    console.log('importChapter.disabled =', importChapter.disabled);
    console.log('importChapter options sample =', importChapter.innerHTML.substring(0, 150));
    if (importChapter.disabled === false && importChapter.innerHTML.includes('অধ্যায়')) {
        console.log('✓ Subject 47 successfully UNLOCKED chapters and populated chapters!');
    } else {
        console.error('✗ Chapter failed to unlock!');
        process.exit(1);
    }

    // 3. User selects Chapter 210
    console.log('\nStep 3: Selecting Chapter 210');
    importChapter.value = '210';
    await importChapter.listeners['change'][0]();

    console.log('importTopic.disabled =', importTopic.disabled);
    console.log('importTopic options sample =', importTopic.innerHTML.substring(0, 150));
    if (importTopic.disabled === false) {
        console.log('✓ Chapter 210 successfully UNLOCKED topics!');
    } else {
        console.error('✗ Topic failed to unlock!');
        process.exit(1);
    }

    console.log('\nALL CASCADING DROPDOWNS UNLOCKED AND VERIFIED SUCCESSFULLY!');
}

testCascade().catch(err => {
    console.error('Test error:', err);
    process.exit(1);
});
