// Global Application State
let tracks = [];
let currentTrack = null;
let cars = [];
let currentCar = null;
let settings = {};
let universalStartSteps = [];
let postRaceSteps = [];
let selectedStep = null;
let activeSequence = "universal_start";
let statusInterval = null;
let isDriving = false;
let rankingsData = [];
let rankingsSortCol = "cr";
let rankingsSortOrder = "desc";
let globalCars = [];
let currentGlobalCar = null;
let currentModalStep = 1;
let modalSelectedTrackId = null;
let modalSelectedCarSetupId = null;
let modalAutoEnableAutoDriveValue = false;
let consoleActionsList = [];
let maxActionIdxReached = 0;
let lastRunCount = 0;


// DOM Elements
const trackList = document.getElementById("trackList");
const addTrackBtn = document.getElementById("addTrackBtn");
const delTrackBtn = document.getElementById("delTrackBtn");
const navTabs = document.querySelectorAll(".nav-tab");
const tabContents = document.querySelectorAll(".tab-content");

// Drive Console DOM elements
const activeTrackTitle = document.getElementById("activeTrackTitle");
const activeTrackType = document.getElementById("activeTrackType");
const activeCarCombo = document.getElementById("activeCarCombo");
const consoleCarImg = document.getElementById("consoleCarImg");
const consoleTrackImg = document.getElementById("consoleTrackImg");
const startDriveBtn = document.getElementById("startDriveBtn");
const stopDriveBtn = document.getElementById("stopDriveBtn");
const statusPhase = document.getElementById("statusPhase");
const statusDesc = document.getElementById("statusDesc");
const statusProgress = document.getElementById("statusProgress");
const timeRemaining = document.getElementById("timeRemaining");
const driveStateIndicator = document.getElementById("driveStateIndicator");

// Session summary DOM elements
const statRuns = document.getElementById("statRuns");
const statCr = document.getElementById("statCr");
const statXp = document.getElementById("statXp");
const statSkills = document.getElementById("statSkills");

// Profile Manager DOM elements
const managerProfileTitle = document.getElementById("managerProfileTitle");
const managerCarCombo = document.getElementById("managerCarCombo");
const addCarBtn = document.getElementById("addCarBtn");
const delCarBtn = document.getElementById("delCarBtn");
const carNameInput = document.getElementById("carNameInput");
const timeMinInput = document.getElementById("timeMinInput");
const timeSecInput = document.getElementById("timeSecInput");
const carXpInput = document.getElementById("carXpInput");
const carCrInput = document.getElementById("carCrInput");
const carSpInput = document.getElementById("carSpInput");
const driftSettingsBox = document.getElementById("driftSettingsBox");
const driftIntervalInput = document.getElementById("driftIntervalInput");
const driftDurationInput = document.getElementById("driftDurationInput");
const driftButtonSelect = document.getElementById("driftButtonSelect");
const saveCarBtn = document.getElementById("saveCarBtn");
const uploadImgBtn = document.getElementById("uploadImgBtn");
const carImageFileInput = document.getElementById("carImageFileInput");
const managerCarImg = document.getElementById("managerCarImg");
const managerTrackImg = document.getElementById("managerTrackImg");

// Yield Stats DOM elements
const calcRuns = document.getElementById("calcRuns");
const calcCr = document.getElementById("calcCr");
const calcXp = document.getElementById("calcXp");
const calcSkills = document.getElementById("calcSkills");

// Settings Tab DOM elements
const focusEnabledCheckbox = document.getElementById("focusEnabledCheckbox");
const startupDelayInput = document.getElementById("startupDelayInput");
const startupDelayVal = document.getElementById("startupDelayVal");
const activationEnabledCheckbox = document.getElementById("activationEnabledCheckbox");
const activationDelayInput = document.getElementById("activationDelayInput");
const activationDelayVal = document.getElementById("activationDelayVal");
const keybindForm = document.getElementById("keybindForm");
const saveBindingsBtn = document.getElementById("saveBindingsBtn");

// Sequence Editor DOM elements
const sequenceSwitchSelect = document.getElementById("sequenceSwitchSelect");
const sequenceStepsList = document.getElementById("sequenceStepsList");
const sequenceEditorHeader = document.getElementById("sequenceEditorHeader");
const stepEditorTitle = document.getElementById("stepEditorTitle");
const stepLabelInput = document.getElementById("stepLabelInput");
const stepTypeSelect = document.getElementById("stepTypeSelect");
const stepValueSelect = document.getElementById("stepValueSelect");
const stepRepsInput = document.getElementById("stepRepsInput");
const stepDelayInput = document.getElementById("stepDelayInput");
const clearStepBtn = document.getElementById("clearStepBtn");
const saveStepBtn = document.getElementById("saveStepBtn");

// Checklist Modal DOM elements
const checklistModal = document.getElementById("checklistModal");
const modalSubInfo = document.getElementById("modalSubInfo");
const modalChecklistItems = document.getElementById("modalChecklistItems");
const modalCancelBtn = document.getElementById("modalCancelBtn");
const modalNextBtn = document.getElementById("modalNextBtn");
const modalForegroundBtn = document.getElementById("modalForegroundBtn");
const modalBackgroundBtn = document.getElementById("modalBackgroundBtn");
const modalWarningText = document.getElementById("modalWarningText");

// Toast DOM element
const toast = document.getElementById("toast");
const carCrMultiplierInput = document.getElementById("carCrMultiplierInput");

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    await fetchTracks();
    await fetchSettings();
    await fetchSequence("universal_start");
    await fetchSequence("post_race");
    
    // Select first track if available
    if (tracks.length > 0) {
        selectTrack(tracks[0].id);
    }
}

// --- EVENT LISTENERS ---
function setupEventListeners() {
    // Navigation Tabs Switching
    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            if (isDriving) return; // Prevent changing tabs while bot runs
            
            navTabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            tab.classList.add("active");
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
            
            // Re-fetch sequence step lists on switching to sequences
            if (tab.dataset.tab === "macros") {
                renderSequenceSteps();
            } else if (tab.dataset.tab === "rankings") {
                fetchAndRenderRankings();
            } else if (tab.dataset.tab === "cars") {
                fetchGlobalCars();
            }
        });
    });

    // Add Track Dialog
    addTrackBtn.addEventListener("click", openTrackCreateDialog);
    delTrackBtn.addEventListener("click", deleteTrackClick);

    // Track Creation Modal actions
    document.getElementById("trackCreateCancelBtn").addEventListener("click", closeTrackCreateDialog);
    document.getElementById("trackCreateConfirmBtn").addEventListener("click", confirmTrackCreate);

    // Car Combobox selections
    activeCarCombo.addEventListener("change", (e) => {
        const selected = cars.find(c => c.name === e.target.value);
        if (selected) selectCar(selected.id);
    });

    managerCarCombo.addEventListener("change", (e) => {
        const selected = cars.find(c => c.name === e.target.value);
        if (selected) selectCar(selected.id);
    });

    // Profile Management
    const addTrackCarBtn = document.getElementById("addTrackCarBtn");
    if (addTrackCarBtn) {
        addTrackCarBtn.addEventListener("click", openCarSetupAddDialog);
    }
    delCarBtn.addEventListener("click", deleteCarClick);
    saveCarBtn.addEventListener("click", saveCarClick);

    // Car Setup Add Modal actions
    document.getElementById("carSetupAddCancelBtn").addEventListener("click", closeCarSetupAddDialog);
    document.getElementById("carSetupAddConfirmBtn").addEventListener("click", confirmCarSetupAdd);

    // Global Cars Manager listeners
    const addGlobalCarBtn = document.getElementById("addGlobalCarBtn");
    const delGlobalCarBtn = document.getElementById("delGlobalCarBtn");
    const saveGlobalCarBtn = document.getElementById("saveGlobalCarBtn");
    const uploadGlobalCarImgBtn = document.getElementById("uploadGlobalCarImgBtn");
    const globalCarImg = document.getElementById("globalCarImg");
    const globalCarImageFileInput = document.getElementById("globalCarImageFileInput");

    if (addGlobalCarBtn) addGlobalCarBtn.addEventListener("click", openGlobalCarCreateDialog);
    if (delGlobalCarBtn) delGlobalCarBtn.addEventListener("click", deleteGlobalCarClick);
    if (saveGlobalCarBtn) saveGlobalCarBtn.addEventListener("click", saveGlobalCarClick);
    if (uploadGlobalCarImgBtn) uploadGlobalCarImgBtn.addEventListener("click", () => globalCarImageFileInput.click());
    if (globalCarImg) globalCarImg.addEventListener("click", () => globalCarImageFileInput.click());
    if (globalCarImageFileInput) globalCarImageFileInput.addEventListener("change", handleGlobalCarImageUpload);

    // Global Car Create Modal actions
    document.getElementById("globalCarCreateCancelBtn").addEventListener("click", closeGlobalCarCreateDialog);
    document.getElementById("globalCarCreateConfirmBtn").addEventListener("click", confirmGlobalCarCreate);

    // Profile inputs changed -> recalculate yield stats real-time
    const inputsToTriggerStats = [
        carNameInput, timeMinInput, timeSecInput, carXpInput, carCrInput, carCrMultiplierInput, carSpInput,
        driftIntervalInput, driftDurationInput, driftButtonSelect
    ];
    inputsToTriggerStats.forEach(input => {
        if (input) input.addEventListener("input", calculateYield);
    });

    // Image Upload
    uploadImgBtn.addEventListener("click", () => carImageFileInput.click());
    managerCarImg.addEventListener("click", () => carImageFileInput.click());
    carImageFileInput.addEventListener("change", handleImageUpload);

    // Global Settings Sliders
    startupDelayInput.addEventListener("input", (e) => {
        startupDelayVal.textContent = `${e.target.value}s`;
        saveGlobalSettings();
    });

    activationDelayInput.addEventListener("input", (e) => {
        activationDelayVal.textContent = `${parseFloat(e.target.value).toFixed(1)}s`;
        saveGlobalSettings();
    });

    const raceTimeBufferInput = document.getElementById("raceTimeBufferInput");
    const raceTimeBufferVal = document.getElementById("raceTimeBufferVal");
    if (raceTimeBufferInput && raceTimeBufferVal) {
        raceTimeBufferInput.addEventListener("input", (e) => {
            raceTimeBufferVal.textContent = `${e.target.value}s`;
            saveGlobalSettings();
        });
    }

    focusEnabledCheckbox.addEventListener("change", saveGlobalSettings);
    activationEnabledCheckbox.addEventListener("change", saveGlobalSettings);
    saveBindingsBtn.addEventListener("click", saveKeybindings);

    // Sequence Switching
    sequenceSwitchSelect.addEventListener("change", (e) => {
        activeSequence = e.target.value;
        clearStepEditor();
        renderSequenceSteps();
    });

    // Step type changed -> reload values
    stepTypeSelect.addEventListener("change", (e) => {
        populateActionValueOptions(e.target.value);
    });

    clearStepBtn.addEventListener("click", clearStepEditor);
    saveStepBtn.addEventListener("click", saveStepClick);

    // Driving Controllers
    startDriveBtn.addEventListener("click", startDriveClick);
    stopDriveBtn.addEventListener("click", stopDriveClick);

    // Multi-step checklist modal controls
    const modalCloseX = document.getElementById("modalCloseX");
    const modalBackBtn = document.getElementById("modalBackBtn");
    const modalNextBtn = document.getElementById("modalNextBtn");
    
    if (modalCloseX) {
        modalCloseX.addEventListener("click", () => {
            checklistModal.classList.remove("active");
        });
    }
    // Close when clicking outside of the modal card
    if (checklistModal) {
        checklistModal.addEventListener("click", (e) => {
            if (e.target === checklistModal) {
                checklistModal.classList.remove("active");
            }
        });
    }
    if (modalBackBtn) {
        modalBackBtn.addEventListener("click", handleModalBackBtnClick);
    }
    if (modalNextBtn) {
        modalNextBtn.addEventListener("click", handleModalNextBtnClick);
    }

    const modalForegroundBtn = document.getElementById("modalForegroundBtn");
    const modalBackgroundBtn = document.getElementById("modalBackgroundBtn");
    if (modalForegroundBtn) {
        modalForegroundBtn.addEventListener("click", () => {
            confirmAndLaunchDrive("Foreground");
        });
    }
    if (modalBackgroundBtn) {
        modalBackgroundBtn.addEventListener("click", () => {
            confirmAndLaunchDrive("Background");
        });
    }

    const modalAutoDriveToggle = document.getElementById("modalAutoDriveToggle");
    if (modalAutoDriveToggle) {
        modalAutoDriveToggle.addEventListener("click", () => {
            modalAutoEnableAutoDriveValue = !modalAutoEnableAutoDriveValue;
            if (modalAutoEnableAutoDriveValue) {
                modalAutoDriveToggle.classList.add("active");
                modalAutoDriveToggle.querySelector(".toggle-text").textContent = "Enable AutoDrive";
            } else {
                modalAutoDriveToggle.classList.remove("active");
                modalAutoDriveToggle.querySelector(".toggle-text").textContent = "Dont enable AutoDrive";
            }
            const track = tracks.find(t => t.id === modalSelectedTrackId);
            if (track) renderChecklistForModal(track);
        });
    }

    // DisplayFusion help button
    const focusHelpIcon = document.getElementById("focusHelpIcon");
    if (focusHelpIcon) {
        focusHelpIcon.addEventListener("click", (e) => {
            e.preventDefault();
            document.getElementById("displayFusionModal").classList.add("active");
        });
    }

    // Track Image Upload
    const uploadTrackImgBtn = document.getElementById("uploadTrackImgBtn");
    const trackImageFileInput = document.getElementById("trackImageFileInput");
    const managerTrackImgBtn = document.getElementById("managerTrackImg");
    if (uploadTrackImgBtn && trackImageFileInput && managerTrackImgBtn) {
        uploadTrackImgBtn.addEventListener("click", () => trackImageFileInput.click());
        managerTrackImgBtn.addEventListener("click", () => trackImageFileInput.click());
        trackImageFileInput.addEventListener("change", handleTrackImageUpload);
    }

    // Rankings sorting
    const headers = document.querySelectorAll(".sortable-header");
    headers.forEach(h => {
        h.addEventListener("click", () => {
            const col = h.dataset.sort;
            if (rankingsSortCol === col) {
                rankingsSortOrder = rankingsSortOrder === "asc" ? "desc" : "asc";
            } else {
                rankingsSortCol = col;
                rankingsSortOrder = "desc";
            }
            sortAndRenderRankingsTable();
        });
    });
}

// --- API FETCHES ---
async function fetchTracks() {
    try {
        const res = await fetch("/api/tracks");
        tracks = await res.json();
        renderTrackList();
    } catch (err) {
        console.error("Error fetching tracks:", err);
    }
}

async function fetchSettings() {
    try {
        const res = await fetch("/api/settings");
        settings = await res.json();
        populateSettingsForm();
    } catch (err) {
        console.error("Error fetching settings:", err);
    }
}

async function fetchSequence(name) {
    try {
        const res = await fetch(`/api/sequences/${name}`);
        const steps = await res.json();
        if (name === "universal_start") {
            universalStartSteps = steps;
        } else {
            postRaceSteps = steps;
        }
    } catch (err) {
        console.error(`Error fetching sequence ${name}:`, err);
    }
}

// --- RENDERING ---
function renderTrackList() {
    trackList.innerHTML = "";
    tracks.forEach(track => {
        const item = document.createElement("button");
        item.className = "track-item";
        if (currentTrack && currentTrack.id === track.id) {
            item.classList.add("active");
        }
        
        let typeBadgeClass = "badge-race";
        if (track.type === "Time Attack") typeBadgeClass = "badge-time_attack";
        else if (track.type === "Drift") typeBadgeClass = "badge-drift";
        
        item.innerHTML = `
            <span class="track-name">${track.name}</span>
            <span class="badge ${typeBadgeClass}">${track.type.substring(0, 2).toUpperCase()}</span>
        `;
        
        item.addEventListener("click", () => selectTrack(track.id));
        trackList.appendChild(item);
    });
}

function selectTrack(trackId, selectedCarId = null) {
    currentTrack = tracks.find(t => t.id === trackId);
    if (!currentTrack) return;
    
    // Highlight track button in sidebar
    const items = trackList.querySelectorAll(".track-item");
    tracks.forEach((t, idx) => {
        if (items[idx]) {
            if (t.id === trackId) items[idx].classList.add("active");
            else items[idx].classList.remove("active");
        }
    });

    // Update Console Titles
    activeTrackTitle.textContent = currentTrack.name;
    activeTrackType.textContent = currentTrack.type;
    activeTrackType.className = `badge badge-${currentTrack.type.toLowerCase().replace(" ", "_")}`;
    
    // Show/Hide Drift Configs
    if (currentTrack.type === "Drift") {
        driftSettingsBox.style.display = "block";
    } else {
        driftSettingsBox.style.display = "none";
    }
    
    // Load track cars
    loadCars(trackId, selectedCarId);
}

async function loadCars(trackId, selectedCarId = null) {
    try {
        const res = await fetch(`/api/tracks/${trackId}/cars`);
        cars = await res.json();
        
        // Populate car dropdowns
        activeCarCombo.innerHTML = "";
        managerCarCombo.innerHTML = "";
        
        if (cars.length > 0) {
            cars.forEach(car => {
                const opt1 = document.createElement("option");
                opt1.value = car.name;
                opt1.textContent = car.name;
                activeCarCombo.appendChild(opt1);
                
                const opt2 = document.createElement("option");
                opt2.value = car.name;
                opt2.textContent = car.name;
                managerCarCombo.appendChild(opt2);
            });
            
            // Select specified car profile or first
            const idToSelect = selectedCarId && cars.some(c => c.id === selectedCarId) 
                ? selectedCarId 
                : cars[0].id;
            selectCar(idToSelect);
        } else {
            activeCarCombo.innerHTML = "<option>-- No Cars --</option>";
            managerCarCombo.innerHTML = "<option>-- No Cars --</option>";
            currentCar = null;
            clearCarForm();
        }
    } catch (err) {
        console.error("Error loading track cars:", err);
    }
}

function selectCar(carId) {
    currentCar = cars.find(c => c.id === carId);
    if (!currentCar) return;
    
    activeCarCombo.value = currentCar.name;
    managerCarCombo.value = currentCar.name;
    
    // Fill Form details
    managerProfileTitle.textContent = `Car profile: ${currentCar.name}`;
    carNameInput.value = currentCar.name;
    
    // Seconds to min/sec
    const totalSecs = currentCar.time_seconds || 0;
    timeMinInput.value = Math.floor(totalSecs / 60);
    timeSecInput.value = totalSecs % 60;
    
    carXpInput.value = currentCar.xp || 0;
    carCrInput.value = currentCar.cr || 0;
    if (carCrMultiplierInput) {
        carCrMultiplierInput.value = currentCar.cr_multiplier !== undefined ? currentCar.cr_multiplier * 100 : 0;
    }
    carSpInput.value = currentCar.skillpoints || 0;
    
    // Drift configs
    driftIntervalInput.value = currentCar.drift_interval || 0.7;
    driftDurationInput.value = currentCar.drift_duration || 0.1;
    driftButtonSelect.value = currentCar.drift_button || "A_BTN";
    
    // Render Images
    updateImages();
    
    // Dynamic Stats calc
    calculateYield();
}

function clearCarForm() {
    managerProfileTitle.textContent = "Track: -- | Car Profile";
    carNameInput.value = "";
    timeMinInput.value = "";
    timeSecInput.value = "";
    carXpInput.value = "";
    carCrInput.value = "";
    if (carCrMultiplierInput) carCrMultiplierInput.value = "";
    carSpInput.value = "";
    
    consoleCarImg.style.backgroundImage = "none";
    consoleCarImg.innerHTML = '<div class="placeholder-text">No image uploaded</div>';
    managerCarImg.style.backgroundImage = "none";
    managerCarImg.innerHTML = '<div class="placeholder-text">Click below to upload a profile picture</div>';
    
    updateYieldLabels(0, 0, 0, 0, 0);
}

function updateImages() {
    // 1. Update Track Image
    if (currentTrack) {
        const trackPath = currentTrack.image_path;
        if (trackPath) {
            consoleTrackImg.style.backgroundImage = `url('${trackPath}')`;
            consoleTrackImg.innerHTML = `<span class="viewport-badge">Track</span>`;
            
            managerTrackImg.style.backgroundImage = `url('${trackPath}')`;
            managerTrackImg.innerHTML = "";
        } else {
            consoleTrackImg.style.backgroundImage = "none";
            consoleTrackImg.innerHTML = `
                <span class="viewport-badge">Track</span>
                <div class="placeholder-text">No track image</div>
            `;
            
            managerTrackImg.style.backgroundImage = "none";
            managerTrackImg.innerHTML = '<div class="placeholder-text">Click to upload track banner</div>';
        }
    }
    
    // 2. Update Car Image
    if (currentCar) {
        const carPath = currentCar.image_path;
        if (carPath) {
            consoleCarImg.style.backgroundImage = `url('${carPath}')`;
            consoleCarImg.innerHTML = `<span class="viewport-badge">Car</span>`;
            
            managerCarImg.style.backgroundImage = `url('${carPath}')`;
            managerCarImg.innerHTML = "";
        } else {
            consoleCarImg.style.backgroundImage = "none";
            consoleCarImg.innerHTML = `
                <span class="viewport-badge">Car</span>
                <div class="placeholder-text">No car image</div>
            `;
            
            managerCarImg.style.backgroundImage = "none";
            managerCarImg.innerHTML = '<div class="placeholder-text">Click below to upload a profile picture</div>';
        }
    } else {
        consoleCarImg.style.backgroundImage = "none";
        consoleCarImg.innerHTML = `
            <span class="viewport-badge">Car</span>
            <div class="placeholder-text">No car image</div>
        `;
        
        managerCarImg.style.backgroundImage = "none";
        managerCarImg.innerHTML = '<div class="placeholder-text">Click below to upload a profile picture</div>';
    }
}

// --- DYNAMIC CALCULATIONS ---
function calculateYield() {
    if (!currentCar || !currentTrack) return;
    
    const timeMin = parseInt(timeMinInput.value || 0);
    const timeSec = parseInt(timeSecInput.value || 0);
    const timeSeconds = timeMin * 60 + timeSec;
    
    if (timeSeconds <= 0) {
        updateYieldLabels(0, 0, 0, 0, 0);
        return;
    }
    
    const xp = parseInt(carXpInput.value || 0);
    const enteredCr = parseInt(carCrInput.value || 0);
    const multPercent = parseFloat(carCrMultiplierInput ? (carCrMultiplierInput.value || 0) : 0);
    
    // Normalization to +100% logic:
    // enteredCr represents base * (1 + multPercent / 100).
    // Target +100% CR is base * 2.
    // base = enteredCr / (1 + multPercent / 100).
    // normalizedCr (at +100%) = base * 2 = enteredCr * 2 / (1 + multPercent / 100).
    const normalizedCr = enteredCr * 2 / (1 + (multPercent / 100));
    const cr = normalizedCr;
    
    const skillpoints = parseInt(carSpInput.value || 0);
    
    const raceBuffer = parseFloat(settings.race_time_buffer || 15);
    let totalLoopTime = timeSeconds + raceBuffer;
    
    if (currentTrack.type === "Race") {
        // Calculate overheads
        let startOverhead = 0;
        universalStartSteps.forEach(step => {
            const rep = step.repetitions || 1;
            const actionDur = (step.action_type === 'button' || step.action_type === 'stick') ? 0.4 : 0;
            startOverhead += (actionDur * rep) + (step.delay || 0);
        });
        
        let postOverhead = 0;
        postRaceSteps.forEach(step => {
            const rep = step.repetitions || 1;
            const actionDur = (step.action_type === 'button' || step.action_type === 'stick') ? 0.4 : 0;
            postOverhead += (actionDur * rep) + (step.delay || 0);
        });
        
        const focusEnabled = focusEnabledCheckbox.checked;
        const focusOverhead = focusEnabled ? 1.0 : 0.0;
        const startupDelay = parseFloat(startupDelayInput.value || 5);
        
        let activationDelay = 0;
        if (activationEnabledCheckbox.checked) {
            activationDelay = parseFloat(activationDelayInput.value || 5) + 0.8;
        }
        
        totalLoopTime = startOverhead + activationDelay + timeSeconds + raceBuffer + postOverhead + startupDelay + focusOverhead;
    }
    
    if (totalLoopTime <= 0) {
        updateYieldLabels(0, 0, 0, 0, 0);
        return;
    }
    
    const runsPerHour = 3600 / totalLoopTime;
    const crPerHour = runsPerHour * cr;
    const xpPerHour = runsPerHour * xp;
    const spPerHour = runsPerHour * skillpoints;
    const skillsPerHour = spPerHour / 50000;
    
    updateYieldLabels(runsPerHour, crPerHour, xpPerHour, spPerHour, skillsPerHour);
}

function updateYieldLabels(runs, cr, xp, sp, skills) {
    calcRuns.textContent = `${runs.toFixed(2)} runs`;
    calcCr.textContent = `${Math.floor(cr).toLocaleString()} CR`;
    calcXp.textContent = `${Math.floor(xp).toLocaleString()} XP`;
    calcSkills.textContent = `${skills.toFixed(2)} (${Math.floor(sp).toLocaleString()} SP)`;
}

// --- TRACK CRUD CALLBACKS ---
function openTrackCreateDialog() {
    const inputEl = document.getElementById("newTrackName");
    if (inputEl) inputEl.value = "";
    document.getElementById("trackCreateModal").classList.add("active");
}

function closeTrackCreateDialog() {
    document.getElementById("trackCreateModal").classList.remove("active");
}

async function confirmTrackCreate() {
    const inputEl = document.getElementById("newTrackName");
    const selectEl = document.getElementById("newTrackType");
    if (!inputEl || inputEl.value.trim() === "") {
        alert("Please enter a track name.");
        return;
    }
    
    const name = inputEl.value.trim();
    const type = selectEl.value;
    
    try {
        const res = await fetch("/api/tracks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, type })
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById("trackCreateModal").classList.remove("active");
            await fetchTracks();
            selectTrack(data.id);
            showToast("Track created successfully!");
        } else {
            alert(data.detail || "Error adding track.");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteTrackClick() {
    if (!currentTrack) return;
    const res = confirm(`Are you sure you want to delete track '${currentTrack.name}'? This deletes all associated car profiles.`);
    if (!res) return;
    
    try {
        const response = await fetch(`/api/tracks/${currentTrack.id}`, { method: "DELETE" });
        if (response.ok) {
            await fetchTracks();
            if (tracks.length > 0) selectTrack(tracks[0].id);
            else clearCarForm();
            showToast("Track deleted.");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- CAR CRUD CALLBACKS ---
async function openCarSetupAddDialog() {
    if (!currentTrack) {
        alert("Please select or add a track first.");
        return;
    }
    const selectEl = document.getElementById("addSetupGlobalCarSelect");
    if (!selectEl) return;
    
    try {
        const res = await fetch("/api/global-cars");
        const library = await res.json();
        
        selectEl.innerHTML = "";
        if (library.length > 0) {
            library.forEach(car => {
                const opt = document.createElement("option");
                opt.value = car.id;
                opt.textContent = car.name;
                selectEl.appendChild(opt);
            });
            document.getElementById("carSetupAddConfirmBtn").disabled = false;
        } else {
            selectEl.innerHTML = "<option value=''>-- No Global Cars Available --</option>";
            document.getElementById("carSetupAddConfirmBtn").disabled = true;
        }
        
        document.getElementById("carSetupAddModal").classList.add("active");
    } catch (err) {
        console.error("Error opening add car setup dialog:", err);
    }
}

function closeCarSetupAddDialog() {
    document.getElementById("carSetupAddModal").classList.remove("active");
}

async function confirmCarSetupAdd() {
    const selectEl = document.getElementById("addSetupGlobalCarSelect");
    if (!selectEl || !currentTrack) return;
    
    const globalCarId = parseInt(selectEl.value);
    if (!globalCarId) {
        alert("Please select a car model.");
        return;
    }
    
    try {
        const res = await fetch("/api/cars", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ track_id: currentTrack.id, global_car_id: globalCarId })
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById("carSetupAddModal").classList.remove("active");
            await loadCars(currentTrack.id);
            selectCar(data.id);
            showToast("Added car setup to track!");
        } else {
            alert(data.detail || "Error adding setup.");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteCarClick() {
    if (!currentCar) return;
    const res = confirm(`Delete car profile '${currentCar.name}'?`);
    if (!res) return;
    
    try {
        const response = await fetch(`/api/cars/${currentCar.id}`, { method: "DELETE" });
        if (response.ok) {
            await loadCars(currentTrack.id);
            showToast("Car profile removed.");
        }
    } catch (err) {
        console.error(err);
    }
}

async function saveCarClick() {
    if (!currentCar) return;
    
    const timeMin = parseInt(timeMinInput.value || 0);
    const timeSec = parseInt(timeSecInput.value || 0);
    const timeSeconds = timeMin * 60 + timeSec;
    
    const multPercent = parseFloat(carCrMultiplierInput ? (carCrMultiplierInput.value || 0) : 0);
    const payload = {
        name: carNameInput.value.trim(),
        time_seconds: timeSeconds,
        xp: parseInt(carXpInput.value || 0),
        cr: parseInt(carCrInput.value || 0),
        cr_multiplier: multPercent / 100.0,
        skillpoints: parseInt(carSpInput.value || 0),
        drift_interval: currentTrack.type === "Drift" ? parseFloat(driftIntervalInput.value || 0.7) : null,
        drift_duration: currentTrack.type === "Drift" ? parseFloat(driftDurationInput.value || 0.1) : null,
        drift_button: currentTrack.type === "Drift" ? driftButtonSelect.value : null,
        image_path: currentCar.image_path
    };
    
    try {
        const res = await fetch(`/api/cars/${currentCar.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const prevId = currentCar.id;
            await loadCars(currentTrack.id);
            selectCar(prevId);
            showToast("Changes saved successfully!");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- IMAGE UPLOAD HANDLERS ---
async function handleImageUpload(e) {
    if (!currentCar) return;
    
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch(`/api/cars/${currentCar.id}/image`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            currentCar.image_path = data.image_path;
            updateImages();
            showToast("Image updated!");
        }
    } catch (err) {
        console.error(err);
    }
}

async function handleTrackImageUpload(e) {
    if (!currentTrack) return;
    
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch(`/api/tracks/${currentTrack.id}/image`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            currentTrack.image_path = data.image_path;
            // update in global track list too
            const localTrack = tracks.find(t => t.id === currentTrack.id);
            if (localTrack) localTrack.image_path = data.image_path;
            updateImages();
            showToast("Track image updated!");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- SETTINGS MAPPING CALLBACKS ---
function populateSettingsForm() {
    focusEnabledCheckbox.checked = settings.focus_window_enabled === "True";
    
    const startVal = parseFloat(settings.startup_delay || 5);
    startupDelayInput.value = startVal;
    startupDelayVal.textContent = `${startVal}s`;
    
    activationEnabledCheckbox.checked = settings.autodrive_activation_enabled === "True";
    
    const actVal = parseFloat(settings.autodrive_activation_delay || 5);
    activationDelayInput.value = actVal;
    activationDelayVal.textContent = `${actVal.toFixed(1)}s`;

    const bufferVal = parseInt(settings.race_time_buffer || 15);
    const bufferInput = document.getElementById("raceTimeBufferInput");
    const bufferValSpan = document.getElementById("raceTimeBufferVal");
    if (bufferInput && bufferValSpan) {
        bufferInput.value = bufferVal;
        bufferValSpan.textContent = `${bufferVal}s`;
    }
}

async function saveGlobalSettings() {
    const bufferInput = document.getElementById("raceTimeBufferInput");
    const payload = {
        focus_window_enabled: focusEnabledCheckbox.checked ? "True" : "False",
        startup_delay: startupDelayInput.value,
        autodrive_activation_enabled: activationEnabledCheckbox.checked ? "True" : "False",
        autodrive_activation_delay: activationDelayInput.value,
        race_time_buffer: bufferInput ? bufferInput.value : "15"
    };
    
    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            settings.focus_window_enabled = payload.focus_window_enabled;
            settings.startup_delay = payload.startup_delay;
            settings.autodrive_activation_enabled = payload.autodrive_activation_enabled;
            settings.autodrive_activation_delay = payload.autodrive_activation_delay;
            settings.race_time_buffer = payload.race_time_buffer;
            calculateYield();
        }
    } catch (err) {
        console.error(err);
    }
}

function renderKeybindingForm() {
    // Populate form list
    const roles = [
        ["ACCELERATE", "Accelerate (Gas):"],
        ["BRAKE", "Brake / Reverse:"],
        ["EBRAKE", "E-Brake (Handbrake):"],
        ["ACTIVATE", "Activate / Confirm:"],
        ["START_EVENT", "Start Event Button:"],
        ["ANNA", "ANNA Menu Trigger:"],
        ["AUTODRIVE", "AutoDrive Toggle:"]
    ];
    
    const options = {
        ACCELERATE: ["RT", "LT", "A_BTN", "B_BTN", "X_BTN", "Y_BTN"],
        BRAKE: ["LT", "RT", "A_BTN", "B_BTN", "X_BTN", "Y_BTN"],
        EBRAKE: ["A_BTN", "B_BTN", "X_BTN", "Y_BTN", "LB", "RB"],
        ACTIVATE: ["A_BTN", "B_BTN", "X_BTN", "Y_BTN", "START", "BACK"],
        START_EVENT: ["X_BTN", "A_BTN", "B_BTN", "Y_BTN", "START", "BACK"],
        ANNA: ["DPAD_DOWN", "DPAD_UP", "DPAD_LEFT", "DPAD_RIGHT"],
        AUTODRIVE: ["DPAD_LEFT", "DPAD_RIGHT", "DPAD_UP", "DPAD_DOWN"]
    };
    
    keybindForm.innerHTML = "";
    roles.forEach(([role, label]) => {
        const row = document.createElement("div");
        row.className = "form-row";
        
        const labelEl = document.createElement("label");
        labelEl.textContent = label;
        labelEl.htmlFor = `bind_${role}`;
        
        const select = document.createElement("select");
        select.id = `bind_${role}`;
        select.className = "select-input";
        
        options[role].forEach(opt => {
            const o = document.createElement("option");
            o.value = opt;
            o.textContent = opt;
            select.appendChild(o);
        });
        
        // Load initial binding value
        const val = settings[`control_${role}`] || options[role][0];
        select.value = val;
        
        row.appendChild(labelEl);
        row.appendChild(select);
        keybindForm.appendChild(row);
    });
}

// Override settings triggers render
async function saveKeybindings() {
    const payload = {};
    const roles = ["ACCELERATE", "BRAKE", "EBRAKE", "ACTIVATE", "START_EVENT", "ANNA", "AUTODRIVE"];
    roles.forEach(role => {
        const el = document.getElementById(`bind_${role}`);
        payload[`control_${role}`] = el.value;
    });
    
    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            Object.assign(settings, payload);
            showToast("Gamepad bindings updated!");
        }
    } catch (err) {
        console.error(err);
    }
}

// --- SEQUENCE MACRO STEPS RENDERING & EDITING ---
function renderSequenceSteps() {
    sequenceStepsList.innerHTML = "";
    const steps = activeSequence === "universal_start" ? universalStartSteps : postRaceSteps;
    
    sequenceEditorHeader.textContent = `${activeSequence === 'universal_start' ? 'Start' : 'Post'} Sequence (${steps.length} steps)`;
    
    steps.forEach((step, idx) => {
        const row = document.createElement("div");
        row.className = "step-item-row";
        
        const valTxt = step.action_value.startsWith("ROLE_") ? step.action_value.replace("ROLE_", "") + " (mapped)" : step.action_value;
        let actDesc = `${step.action_type.toUpperCase()}: ${valTxt}`;
        if (step.repetitions > 1) actDesc += ` x${step.repetitions}`;
        if (step.delay > 0) actDesc += ` (+${step.delay}s)`;
        
        row.innerHTML = `
            <div class="step-info">
                <span class="step-num-lbl">#${step.step_index}</span>
                <span class="step-desc-lbl">${step.label}</span>
                <span class="step-action-desc">${actDesc}</span>
            </div>
            <div class="step-controls">
                <button class="btn btn-neutral btn-icon" onclick="moveStepClick(${idx}, -1)">▲</button>
                <button class="btn btn-neutral btn-icon" onclick="moveStepClick(${idx}, 1)">▼</button>
                <button class="btn btn-danger btn-icon" onclick="deleteStepClick(${idx})">×</button>
            </div>
        `;
        
        // Clicking step details populates form
        row.querySelector(".step-info").addEventListener("click", () => selectStep(step));
        sequenceStepsList.appendChild(row);
    });
    
    // Reload bindings layout
    renderKeybindingForm();
}

function selectStep(step) {
    selectedStep = step;
    stepEditorTitle.textContent = `Editing Step #${step.step_index}`;
    
    stepLabelInput.value = step.label;
    stepTypeSelect.value = step.action_type;
    populateActionValueOptions(step.action_type);
    stepValueSelect.value = step.action_value;
    stepRepsInput.value = step.repetitions;
    stepDelayInput.value = step.delay;
    
    saveStepBtn.textContent = "💾 Update Step";
    saveStepBtn.className = "btn btn-primary";
}

function clearStepEditor() {
    selectedStep = null;
    stepEditorTitle.textContent = "Step Editor (Add New Step)";
    
    stepLabelInput.value = "";
    stepTypeSelect.value = "button";
    populateActionValueOptions("button");
    stepRepsInput.value = "1";
    stepDelayInput.value = "0.0";
    
    saveStepBtn.textContent = "💾 Save Step";
    saveStepBtn.className = "btn btn-success";
}

function populateActionValueOptions(type) {
    stepValueSelect.innerHTML = "";
    let opts = [];
    if (type === "button") {
        opts = [
            "ROLE_ACTIVATE", "ROLE_START_EVENT", "ROLE_ANNA", "ROLE_AUTODRIVE", "ROLE_EBRAKE",
            "A_BTN", "B_BTN", "X_BTN", "Y_BTN", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
            "START", "BACK", "LB", "RB"
        ];
    } else if (type === "stick") {
        opts = ["STICK_UP", "STICK_DOWN", "STICK_LEFT", "STICK_RIGHT"];
    } else {
        opts = ["NONE"];
    }
    
    opts.forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        stepValueSelect.appendChild(o);
    });
}

async function saveStepClick() {
    const label = stepLabelInput.value.trim() || "Macro Action";
    const type = stepTypeSelect.value;
    const value = stepValueSelect.value;
    const reps = parseInt(stepRepsInput.value || 1);
    const delay = parseFloat(stepDelayInput.value || 0.0);
    
    const steps = activeSequence === "universal_start" ? universalStartSteps : postRaceSteps;
    
    if (selectedStep) {
        // Editing existing
        const idx = selectedStep.step_index;
        const target = steps.find(s => s.step_index === idx);
        if (target) {
            target.label = label;
            target.action_type = type;
            target.action_value = value;
            target.repetitions = reps;
            target.delay = delay;
        }
    } else {
        // Appending new step
        steps.push({
            label,
            action_type: type,
            action_value: value,
            repetitions: reps,
            delay
        });
    }
    
    await saveSequenceSteps(steps);
    clearStepEditor();
}

async function saveSequenceSteps(steps) {
    try {
        const res = await fetch(`/api/sequences/${activeSequence}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(steps)
        });
        if (res.ok) {
            if (activeSequence === "universal_start") {
                universalStartSteps = await (await fetch(`/api/sequences/universal_start`)).json();
            } else {
                postRaceSteps = await (await fetch(`/api/sequences/post_race`)).json();
            }
            renderSequenceSteps();
            calculateYield();
            showToast("Sequence saved successfully!");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteStepClick(idx) {
    const steps = activeSequence === "universal_start" ? universalStartSteps : postRaceSteps;
    steps.splice(idx, 1);
    await saveSequenceSteps(steps);
}

async function moveStepClick(idx, direction) {
    const steps = activeSequence === "universal_start" ? universalStartSteps : postRaceSteps;
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= steps.length) return;
    
    // Swap items
    const temp = steps[idx];
    steps[idx] = steps[targetIdx];
    steps[targetIdx] = temp;
    
    await saveSequenceSteps(steps);
}

// Make these functions window accessible since they are in HTML onClick events
window.moveStepClick = moveStepClick;
window.deleteStepClick = deleteStepClick;

// --- AUTO DRIVE ENGINE CONTROLLERS ---
// --- AUTO DRIVE ENGINE CONTROLLERS ---
// --- AUTO DRIVE ENGINE CONTROLLERS ---
async function startDriveClick() {
    currentModalStep = 1;
    // Default to currently selected track/car in the console sidebar
    if (currentTrack) {
        modalSelectedTrackId = currentTrack.id;
    } else if (tracks.length > 0) {
        modalSelectedTrackId = tracks[0].id;
    }
    
    if (currentCar) {
        modalSelectedCarSetupId = currentCar.id;
    } else {
        modalSelectedCarSetupId = null;
    }
    
    // Reset Xbox toggle state on open
    modalAutoEnableAutoDriveValue = false;
    const modalAutoDriveToggle = document.getElementById("modalAutoDriveToggle");
    if (modalAutoDriveToggle) {
        modalAutoDriveToggle.classList.remove("active");
        modalAutoDriveToggle.querySelector(".toggle-text").textContent = "Dont enable AutoDrive";
    }
    
    updateModalStepUI();
    renderModalTrackTiles();
    
    checklistModal.classList.add("active");
}

function updateModalStepUI() {
    // Hide all step pages
    document.querySelectorAll(".modal-step-page").forEach(page => page.classList.remove("active"));
    // Show current page
    document.getElementById(`step-page-${currentModalStep}`).classList.add("active");
    
    // Update progress steps indicators
    document.querySelectorAll(".step-indicator-item").forEach((ind, idx) => {
        ind.classList.remove("active", "completed");
        if (idx + 1 === currentModalStep) {
            ind.classList.add("active");
        } else if (idx + 1 < currentModalStep) {
            ind.classList.add("completed");
        }
    });
    
    // Configure buttons
    const backBtn = document.getElementById("modalBackBtn");
    const nextBtn = document.getElementById("modalNextBtn");
    const fgBtn = document.getElementById("modalForegroundBtn");
    const bgBtn = document.getElementById("modalBackgroundBtn");
    
    // Reset standard styles
    backBtn.textContent = "Back";
    
    if (currentModalStep === 1) {
        backBtn.style.visibility = "hidden";
        nextBtn.style.display = "inline-block";
        nextBtn.textContent = "Next";
        if (fgBtn) fgBtn.style.display = "none";
        if (bgBtn) bgBtn.style.display = "none";
    } else if (currentModalStep === 2) {
        backBtn.style.visibility = "visible";
        nextBtn.style.display = "inline-block";
        nextBtn.textContent = "Next";
        if (fgBtn) fgBtn.style.display = "none";
        if (bgBtn) bgBtn.style.display = "none";
    } else if (currentModalStep === 3) {
        // Back-arrow
        backBtn.style.visibility = "visible";
        backBtn.textContent = "←";
        
        nextBtn.style.display = "none";
        if (fgBtn) fgBtn.style.display = "inline-block";
        if (bgBtn) bgBtn.style.display = "inline-block";
        
        // Hide AutoDrive toggle if NOT a Race type track
        const track = tracks.find(t => t.id === modalSelectedTrackId);
        const toggleEl = document.getElementById("modalAutoDriveToggle");
        if (toggleEl) {
            if (track && track.type === "Race") {
                toggleEl.style.display = "inline-flex";
            } else {
                toggleEl.style.display = "none";
            }
        }
    }
    
    document.getElementById("modalWarningText").textContent = "";
}

async function handleModalNextBtnClick() {
    if (currentModalStep === 1) {
        if (!modalSelectedTrackId) {
            document.getElementById("modalWarningText").textContent = "Please select a track first!";
            return;
        }
        currentModalStep = 2;
        updateModalStepUI();
        await renderModalCarTiles();
    } else if (currentModalStep === 2) {
        if (!modalSelectedCarSetupId) {
            document.getElementById("modalWarningText").textContent = "Please select a car setup first!";
            return;
        }
        currentModalStep = 3;
        updateModalStepUI();
        const track = tracks.find(t => t.id === modalSelectedTrackId);
        if (track) renderChecklistForModal(track);
    }
}

function handleModalBackBtnClick() {
    if (currentModalStep > 1) {
        currentModalStep--;
        updateModalStepUI();
    }
}

function renderModalTrackTiles() {
    const container = document.getElementById("modalTrackTiles");
    if (!container) return;
    
    container.innerHTML = "";
    
    tracks.forEach(track => {
        const tile = document.createElement("div");
        tile.className = "tile-item";
        if (modalSelectedTrackId === track.id) {
            tile.classList.add("selected");
        }
        
        const imgStyle = track.image_path 
            ? `background-image: url('${track.image_path}')` 
            : `background: linear-gradient(135deg, #1e293b, #334155);`;
        const imgContent = track.image_path ? '' : '🏁';
        
        let typeBadgeClass = "badge-race";
        if (track.type === "Time Attack") typeBadgeClass = "badge-time_attack";
        else if (track.type === "Drift") typeBadgeClass = "badge-drift";
        
        tile.innerHTML = `
            <div class="tile-img" style="${imgStyle}">${imgContent}</div>
            <div class="tile-name">${track.name}</div>
            <span class="tile-type badge ${typeBadgeClass}">${track.type}</span>
        `;
        
        tile.addEventListener("click", () => {
            modalSelectedTrackId = track.id;
            container.querySelectorAll(".tile-item").forEach(el => el.classList.remove("selected"));
            tile.classList.add("selected");
            document.getElementById("modalWarningText").textContent = "";
            // Auto-continue to Step 2
            setTimeout(handleModalNextBtnClick, 200);
        });
        
        container.appendChild(tile);
    });
}

async function renderModalCarTiles() {
    const container = document.getElementById("modalCarTiles");
    if (!container) return;
    
    container.innerHTML = "<p style='color: var(--text-secondary); grid-column: 1/-1;'>Loading cars...</p>";
    
    try {
        const res = await fetch(`/api/tracks/${modalSelectedTrackId}/cars`);
        const trackCars = await res.json();
        
        container.innerHTML = "";
        
        if (trackCars.length === 0) {
            container.innerHTML = "<p style='color: var(--accent-red); grid-column: 1/-1; text-align: center; margin-top: 20px;'>No cars configured for this track yet. Add one in Track Setups first.</p>";
            document.getElementById("modalNextBtn").disabled = true;
            return;
        }
        
        document.getElementById("modalNextBtn").disabled = false;
        
        trackCars.forEach(car => {
            const tile = document.createElement("div");
            tile.className = "tile-item";
            if (modalSelectedCarSetupId === car.id) {
                tile.classList.add("selected");
            }
            
            const imgStyle = car.image_path 
                ? `background-image: url('${car.image_path}')` 
                : `background: linear-gradient(135deg, #0f172a, #1e293b);`;
            const imgContent = car.image_path ? '' : '🚗';
            
            tile.innerHTML = `
                <div class="tile-img" style="${imgStyle}">${imgContent}</div>
                <div class="tile-name">${car.name}</div>
                <div style="font-size: 11px; color: var(--text-secondary); font-weight: bold; margin-top: 2px;">
                    ${Math.floor(car.time_seconds / 60)}m ${car.time_seconds % 60}s
                </div>
            `;
            
            tile.addEventListener("click", () => {
                modalSelectedCarSetupId = car.id;
                container.querySelectorAll(".tile-item").forEach(el => el.classList.remove("selected"));
                tile.classList.add("selected");
                document.getElementById("modalWarningText").textContent = "";
                // Auto-continue to Step 3
                setTimeout(handleModalNextBtnClick, 200);
            });
            
            container.appendChild(tile);
        });
        
        // If previous selection is not in the list, clear it
        if (!trackCars.some(c => c.id === modalSelectedCarSetupId)) {
            modalSelectedCarSetupId = null;
        }
    } catch (err) {
        console.error("Error fetching modal car tiles:", err);
        container.innerHTML = "<p style='color: var(--accent-red); grid-column: 1/-1;'>Error loading cars library.</p>";
    }
}

function renderChecklistForModal(track) {
    modalChecklistItems.innerHTML = "";
    
    let items = [];
    if (track.type === "Race") {
        items.push("Teleport / Travel to the starting gate of the event.");
        items.push("Reminder: Set difficulty / assist settings in game to match your +100% CR multiplier target!");
    } else {
        items.push("Teleport / Travel to the starting zone line of the Time Attack / Drift loop.");
        items.push("Reminder: Set all assist options to 'Custom' in the game settings menu (no AutoDrive) so automation executes correctly.");
    }
    
    items.forEach((item, idx) => {
        const row = document.createElement("div");
        row.className = "modal-checklist-item static-warning";
        row.innerHTML = `
            <span class="warning-icon">⚠️</span>
            <span>${item}</span>
        `;
        modalChecklistItems.appendChild(row);
    });
}

function confirmAndLaunchDrive(focusMode) {
    if (!modalSelectedTrackId || !modalSelectedCarSetupId) {
        alert("Please select a Track and Car setup first.");
        return;
    }
    
    // Update main dashboard views too
    selectTrack(modalSelectedTrackId, modalSelectedCarSetupId);
    
    // Build dynamic console actions list
    const track = tracks.find(t => t.id === modalSelectedTrackId);
    const car = cars.find(c => c.id === modalSelectedCarSetupId);
    const autoEnable = modalAutoEnableAutoDriveValue;
    
    consoleActionsList = buildConsoleActionsList(track, car, focusMode, autoEnable);
    maxActionIdxReached = 0;
    lastRunCount = 0;
    renderConsoleActionsListHTML();
    
    // Show checklist and hide default progress
    document.getElementById("runningActionsChecklist").style.display = "flex";
    document.querySelector(".drive-console-card .progress-bar-container").style.display = "none";
    document.querySelector(".drive-console-card .progress-labels").style.display = "none";
    
    checklistModal.classList.remove("active");
    launchDriveWithSetup(modalSelectedTrackId, modalSelectedCarSetupId, focusMode, autoEnable);
}

function buildConsoleActionsList(track, car, focusMode, autoEnable) {
    const actions = [];
    
    // 1. Startup Delay (only if Foreground focus mode)
    if (focusMode === "Foreground") {
        const startupDelay = parseFloat(settings.startup_delay || 5);
        if (startupDelay > 0) {
            actions.push({
                id: "startup_delay",
                label: "Countdown Startup Delay",
                phase: "Startup Delay",
                description: "",
                status: "pending",
                progress: 0
            });
        }
        
        actions.push({
            id: "focus_window",
            label: "Focus Forza Horizon Window",
            phase: "Focus Window",
            description: "",
            status: "pending",
            progress: 0
        });
    }
    
    // 2. Track specific phases
    if (track.type === "Race") {
        // Universal Start Sequence steps
        universalStartSteps.forEach((step) => {
            actions.push({
                id: `start_step_${step.step_index}`,
                label: `Start: ${step.label}`,
                phase: "Universal Start",
                description: `Start: ${step.label}`,
                status: "pending",
                progress: 0
            });
        });
        
        // AutoDrive Activation (if enabled)
        if (autoEnable) {
            actions.push({
                id: "autodrive_activation",
                label: "Auto-Enable Game Autodrive",
                phase: "AutoDrive Activation",
                description: "",
                status: "pending",
                progress: 0
            });
        }
        
        // Active Driving Loop
        actions.push({
            id: "race_active",
            label: "Race Driving Loop",
            phase: "Race Active",
            description: "",
            status: "pending",
            progress: 0
        });
        
        // Post-Race Sequence steps
        postRaceSteps.forEach((step) => {
            actions.push({
                id: `post_step_${step.step_index}`,
                label: `Post-Race: ${step.label}`,
                phase: "Post-Race Sequence",
                description: `Post-Race: ${step.label}`,
                status: "pending",
                progress: 0
            });
        });
    } else if (track.type === "Time Attack") {
        actions.push({
            id: "time_attack_active",
            label: `Driving Time Attack Loop`,
            phase: "Time Attack Active",
            description: "",
            status: "pending",
            progress: 0
        });
    } else if (track.type === "Drift") {
        actions.push({
            id: "drift_active",
            label: `Driving Drift Loop`,
            phase: "Drift Active",
            description: "",
            status: "pending",
            progress: 0
        });
    }
    
    return actions;
}

function renderConsoleActionsListHTML() {
    const container = document.getElementById("runningActionsChecklist");
    if (!container) return;
    
    container.innerHTML = "";
    consoleActionsList.forEach(act => {
        const row = document.createElement("div");
        row.className = `action-row ${act.status}`;
        
        let icon = "⚪";
        if (act.status === "completed") icon = "✔️";
        else if (act.status === "active") icon = "🏎️";
        
        row.innerHTML = `
            <div class="action-row-header">
                <span class="action-icon">${icon}</span>
                <span class="action-label">${act.label}</span>
            </div>
            <div class="action-timer-bar">
                <div class="action-timer-fill" style="width: ${act.progress * 100}%"></div>
            </div>
        `;
        container.appendChild(row);
    });
}

function updateConsoleActionsUI(snap) {
    if (!consoleActionsList || consoleActionsList.length === 0) return;
    
    // Find the current action index
    let currentIdx = -1;
    
    // Start searching from maxActionIdxReached to handle duplicates correctly!
    for (let i = maxActionIdxReached; i < consoleActionsList.length; i++) {
        const act = consoleActionsList[i];
        
        let match = false;
        if (act.phase === snap.phase) {
            if (act.phase === "Universal Start" || act.phase === "Post-Race Sequence") {
                if (snap.description && snap.description.includes(act.description)) {
                    match = true;
                }
            } else {
                match = true;
            }
        }
        
        if (match) {
            currentIdx = i;
            maxActionIdxReached = i;
            break;
        }
    }
    
    // Update states of all actions based on currentIdx
    consoleActionsList.forEach((act, idx) => {
        if (currentIdx !== -1) {
            if (idx < currentIdx) {
                act.status = "completed";
                act.progress = 1.0;
            } else if (idx === currentIdx) {
                act.status = "active";
                act.progress = snap.progress;
            } else {
                act.status = "pending";
                act.progress = 0;
            }
        }
    });
    
    renderConsoleActionsListHTML();
}

async function launchDriveWithSetup(trackId, carSetupId, focusMode, autoEnable) {
    try {
        const res = await fetch("/api/drive/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                track_id: trackId,
                car_id: carSetupId,
                focus_mode: focusMode,
                auto_enable_autodrive: autoEnable
            })
        });
        if (res.ok) {
            isDriving = true;
            toggleUIRunningLock(true);
            showToast("AutoDrive sequence launched!");
            
            // Poll status faster
            if (statusInterval) clearInterval(statusInterval);
            statusInterval = setInterval(pollRunningStatus, 100);
        } else {
            const data = await res.json();
            alert(data.detail || "Failed to start driving.");
        }
    } catch (err) {
        console.error(err);
    }
}

async function stopDriveClick() {
    try {
        const res = await fetch("/api/drive/stop", { method: "POST" });
        if (res.ok) {
            showToast("Stopping virtual controller sequence...");
            stopDriveBtn.disabled = true;
        }
    } catch (err) {
        console.error(err);
    }
}

async function pollRunningStatus() {
    try {
        const res = await fetch("/api/drive/status");
        const snap = await res.json();
        
        if (snap.is_running) {
            isDriving = true;
            toggleUIRunningLock(true);
            
            // If checklist is not populated yet (e.g. reload or back from background), build it
            if (!consoleActionsList || consoleActionsList.length === 0) {
                if (currentTrack && currentCar) {
                    const focusMode = snap.phase === "Startup Delay" || snap.phase === "Focus Window" ? "Foreground" : "Background";
                    const autoEnable = settings.autodrive_activation_enabled === "True";
                    consoleActionsList = buildConsoleActionsList(currentTrack, currentCar, focusMode, autoEnable);
                    maxActionIdxReached = 0;
                    lastRunCount = snap.run_count;
                    renderConsoleActionsListHTML();
                }
                
                document.getElementById("runningActionsChecklist").style.display = "flex";
                document.querySelector(".drive-console-card .progress-bar-container").style.display = "none";
                document.querySelector(".drive-console-card .progress-labels").style.display = "none";
            }
            
            // Check loop restart
            if (snap.run_count !== lastRunCount) {
                maxActionIdxReached = 0;
                lastRunCount = snap.run_count;
            }
            
            updateConsoleActionsUI(snap);
            
            // Update UI Console
            statusPhase.textContent = `STATUS: ${snap.phase.toUpperCase()}`;
            statusDesc.textContent = snap.description;
            statusProgress.style.width = `${snap.progress * 100}%`;
            timeRemaining.textContent = `Time Remaining: ${snap.time_left.toFixed(1)}s`;
            
            // Update Session Stats
            statRuns.textContent = snap.run_count;
            statCr.textContent = `${snap.accumulated_cr.toLocaleString()} CR`;
            statXp.textContent = `${snap.accumulated_xp.toLocaleString()} XP`;
            
            const sp = snap.accumulated_skillpoints;
            statSkills.textContent = `${(sp / 50000).toFixed(2)} (${sp.toLocaleString()} SP)`;
        } else {
            // Stopped
            isDriving = false;
            toggleUIRunningLock(false);
            
            statusPhase.textContent = "SYSTEM STATUS: IDLE";
            statusDesc.textContent = "Select a profile and click Start Driving.";
            statusProgress.style.width = "0%";
            timeRemaining.textContent = "Time Remaining: 0.0s";
            
            // Clear checklist actions
            consoleActionsList = [];
            
            // Hide the running actions checklist and show default progress
            document.getElementById("runningActionsChecklist").style.display = "none";
            document.querySelector(".drive-console-card .progress-bar-container").style.display = "block";
            document.querySelector(".drive-console-card .progress-labels").style.display = "block";
            
            clearInterval(statusInterval);
            statusInterval = null;
            
            if (snap.error_msg) {
                const errMsgLower = snap.error_msg.toLowerCase();
                if (errMsgLower.includes("vigem") || errMsgLower.includes("driver") || errMsgLower.includes("bus not found")) {
                    document.getElementById('driverErrorModal').classList.add('active');
                } else {
                    alert(`Driving loop encountered an error:\n\n${snap.error_msg}`);
                }
            }
        }
    } catch (err) {
        console.error("Error polling driving status:", err);
    }
}

function toggleUIRunningLock(lock) {
    if (lock) {
        document.body.classList.add("running");
        driveStateIndicator.classList.add("running");
        startDriveBtn.disabled = true;
        stopDriveBtn.disabled = false;
        
        // Lock selections & tabs
        activeCarCombo.disabled = true;
        addTrackBtn.disabled = true;
        delTrackBtn.disabled = true;
        document.querySelector(".nav-tabs").setAttribute("disabled", "true");
    } else {
        document.body.classList.remove("running");
        driveStateIndicator.classList.remove("running");
        startDriveBtn.disabled = false;
        stopDriveBtn.disabled = true;
        
        // Unlock
        activeCarCombo.disabled = false;
        addTrackBtn.disabled = false;
        delTrackBtn.disabled = false;
        document.querySelector(".nav-tabs").removeAttribute("disabled");
    }
}

// --- UTILITY TOAST ---
function showToast(message) {
    toast.textContent = message;
    toast.classList.add("active");
    setTimeout(() => {
        toast.classList.remove("active");
    }, 2500);
}

// --- RANKINGS & LEADERBOARD METRICS & RENDERING ---
function computeSetupMetrics(trackType, timeSeconds, cr, cr_multiplier, xp, skillpoints) {
    if (timeSeconds <= 0) {
        return { runs: 0, cr: 0, xp: 0, sp: 0, loopTime: 0 };
    }
    
    // Normalize entered CR to +100% multiplier rate:
    // base = cr / (1 + cr_multiplier)
    // target (+100%) = base * 2 = cr * 2 / (1 + cr_multiplier)
    const multVal = parseFloat(cr_multiplier || 0);
    const normalizedCr = cr * 2 / (1 + multVal);

    const raceBuffer = parseFloat(settings.race_time_buffer || 15);
    let totalLoopTime = timeSeconds + raceBuffer;
    if (trackType === "Race") {
        let startOverhead = 0;
        universalStartSteps.forEach(step => {
            const rep = step.repetitions || 1;
            const actionDur = (step.action_type === 'button' || step.action_type === 'stick') ? 0.4 : 0;
            startOverhead += (actionDur * rep) + (step.delay || 0);
        });
        
        let postOverhead = 0;
        postRaceSteps.forEach(step => {
            const rep = step.repetitions || 1;
            const actionDur = (step.action_type === 'button' || step.action_type === 'stick') ? 0.4 : 0;
            postOverhead += (actionDur * rep) + (step.delay || 0);
        });
        
        const focusEnabled = settings.focus_window_enabled === "True";
        const focusOverhead = focusEnabled ? 1.0 : 0.0;
        const startupDelay = parseFloat(settings.startup_delay || 5);
        
        let activationDelay = 0;
        if (settings.autodrive_activation_enabled === "True") {
            activationDelay = parseFloat(settings.autodrive_activation_delay || 5) + 0.8;
        }
        
        totalLoopTime = startOverhead + activationDelay + timeSeconds + raceBuffer + postOverhead + startupDelay + focusOverhead;
    }
    
    if (totalLoopTime <= 0) {
        return { runs: 0, cr: 0, xp: 0, sp: 0, loopTime: totalLoopTime };
    }
    
    const runsPerHour = 3600 / totalLoopTime;
    const crPerHour = runsPerHour * normalizedCr;
    const xpPerHour = runsPerHour * xp;
    const spPerHour = runsPerHour * skillpoints;
    
    return {
        runs: runsPerHour,
        cr: crPerHour,
        xp: xpPerHour,
        sp: spPerHour,
        loopTime: totalLoopTime
    };
}

async function fetchAndRenderRankings() {
    try {
        const res = await fetch("/api/rankings");
        if (!res.ok) return;
        const rawSetups = await res.json();
        
        // Compute metrics for each setup
        rankingsData = rawSetups.map(setup => {
            const metrics = computeSetupMetrics(
                setup.track_type,
                setup.time_seconds || 0,
                setup.cr || 0,
                setup.cr_multiplier || 0,
                setup.xp || 0,
                setup.skillpoints || 0
            );
            return {
                ...setup,
                metrics
            };
        });
        
        sortAndRenderRankingsTable();
    } catch (err) {
        console.error("Error fetching rankings:", err);
    }
}

function sortAndRenderRankingsTable() {
    // Sort rankingsData by active column
    rankingsData.sort((a, b) => {
        let valA = a.metrics[rankingsSortCol] || 0;
        let valB = b.metrics[rankingsSortCol] || 0;
        
        if (rankingsSortOrder === "asc") {
            return valA - valB;
        } else {
            return valB - valA;
        }
    });
    
    // Render in table body
    const tbody = document.getElementById("rankingsTableBody");
    if (!tbody) return;
    
    tbody.innerHTML = "";
    
    if (rankingsData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">No setups found in database.</td></tr>`;
        return;
    }
    
    rankingsData.forEach(setup => {
        const trackImgStyle = setup.track_image_path 
            ? `background-image: url('${setup.track_image_path}')` 
            : `background: linear-gradient(135deg, #1e293b, #334155); display: flex; align-items: center; justify-content: center; font-size: 8px; color: var(--text-secondary);`;
        const trackImgContent = setup.track_image_path ? '' : 'TR';
        
        const carImgStyle = setup.image_path 
            ? `background-image: url('${setup.image_path}')` 
            : `background: linear-gradient(135deg, #0f172a, #1e293b); display: flex; align-items: center; justify-content: center; font-size: 8px; color: var(--text-secondary);`;
        const carImgContent = setup.image_path ? '' : 'CAR';
        
        const timeMin = Math.floor((setup.time_seconds || 0) / 60);
        const timeSec = Math.floor((setup.time_seconds || 0) % 60);
        const timeStr = `${timeMin}m ${timeSec}s`;
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="table-img-thumb" style="width: 48px; height: 30px; background-size: cover; background-position: center; border-radius: 4px; border: 1px solid var(--border-color); ${trackImgStyle}">${trackImgContent}</div>
                    <span>${setup.track_name}</span>
                </div>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="table-img-thumb" style="width: 48px; height: 30px; background-size: cover; background-position: center; border-radius: 4px; border: 1px solid var(--border-color); ${carImgStyle}">${carImgContent}</div>
                    <span>${setup.name}</span>
                </div>
            </td>
            <td class="highlight-cr">${Math.floor(setup.metrics.cr).toLocaleString()} CR/hr</td>
            <td class="highlight-xp">${Math.floor(setup.metrics.xp).toLocaleString()} XP/hr</td>
            <td class="highlight-sp">${(setup.metrics.sp / 50000).toFixed(2)} (${Math.floor(setup.metrics.sp).toLocaleString()} SP/hr)</td>
            <td style="color: var(--text-secondary);">${timeStr}</td>
            <td>
                <button class="btn btn-primary btn-small" onclick="driveSetupClick(${setup.track_id}, ${setup.id})">🏎️ Drive</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Update header icons
    const headers = document.querySelectorAll(".sortable-header");
    headers.forEach(h => {
        const col = h.dataset.sort;
        h.classList.remove("sorted-asc", "sorted-desc");
        if (col === rankingsSortCol) {
            h.classList.add(rankingsSortOrder === "asc" ? "sorted-asc" : "sorted-desc");
        }
    });
}

// --- GLOBAL CARS MANAGER FUNCTIONS ---
async function fetchGlobalCars() {
    try {
        const res = await fetch("/api/global-cars");
        if (!res.ok) return;
        globalCars = await res.json();
        renderGlobalCarList();
        
        // Select first global car if none is selected
        if (globalCars.length > 0) {
            if (!currentGlobalCar || !globalCars.find(c => c.id === currentGlobalCar.id)) {
                selectGlobalCar(globalCars[0].id);
            } else {
                selectGlobalCar(currentGlobalCar.id);
            }
        } else {
            clearGlobalCarForm();
        }
    } catch (err) {
        console.error("Error fetching global cars:", err);
    }
}

function renderGlobalCarList() {
    const listContainer = document.getElementById("globalCarList");
    if (!listContainer) return;
    listContainer.innerHTML = "";
    
    globalCars.forEach(car => {
        const item = document.createElement("button");
        item.className = "track-item";
        if (currentGlobalCar && currentGlobalCar.id === car.id) {
            item.classList.add("active");
        }
        
        item.innerHTML = `<span class="track-name">${car.name}</span>`;
        item.addEventListener("click", () => selectGlobalCar(car.id));
        listContainer.appendChild(item);
    });
}

function selectGlobalCar(id) {
    currentGlobalCar = globalCars.find(c => c.id === id);
    if (!currentGlobalCar) return;
    
    // Highlight in list
    const listContainer = document.getElementById("globalCarList");
    if (listContainer) {
        const items = listContainer.querySelectorAll(".track-item");
        globalCars.forEach((c, idx) => {
            if (c.id === id) items[idx].classList.add("active");
            else items[idx].classList.remove("active");
        });
    }
    
    // Update Form
    const nameInput = document.getElementById("globalCarNameInput");
    if (nameInput) nameInput.value = currentGlobalCar.name;
    
    // Update Image Preview
    updateGlobalCarImagePreview();
}

function clearGlobalCarForm() {
    currentGlobalCar = null;
    const nameInput = document.getElementById("globalCarNameInput");
    if (nameInput) nameInput.value = "";
    updateGlobalCarImagePreview();
}

function updateGlobalCarImagePreview() {
    const imgDiv = document.getElementById("globalCarImg");
    if (!imgDiv) return;
    
    if (currentGlobalCar && currentGlobalCar.image_path) {
        imgDiv.style.backgroundImage = `url('${currentGlobalCar.image_path}')`;
        imgDiv.innerHTML = "";
    } else {
        imgDiv.style.backgroundImage = "none";
        imgDiv.innerHTML = '<div class="placeholder-text">Click to upload car image</div>';
    }
}

function openGlobalCarCreateDialog() {
    const inputEl = document.getElementById("newGlobalCarName");
    if (inputEl) inputEl.value = "";
    document.getElementById("globalCarCreateModal").classList.add("active");
}

function closeGlobalCarCreateDialog() {
    document.getElementById("globalCarCreateModal").classList.remove("active");
}

async function confirmGlobalCarCreate() {
    const inputEl = document.getElementById("newGlobalCarName");
    if (!inputEl || inputEl.value.trim() === "") {
        alert("Please enter a car name.");
        return;
    }
    
    const name = inputEl.value.trim();
    try {
        const res = await fetch("/api/global-cars", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById("globalCarCreateModal").classList.remove("active");
            await fetchGlobalCars();
            selectGlobalCar(data.id);
            showToast("Car added to global library!");
        } else {
            alert(data.detail || "Error adding car.");
        }
    } catch (err) {
        console.error("Error creating global car:", err);
    }
}

async function deleteGlobalCarClick() {
    if (!currentGlobalCar) return;
    const conf = confirm(`Are you sure you want to delete "${currentGlobalCar.name}"? This removes it from ALL tracks and setup configurations!`);
    if (!conf) return;
    
    try {
        const res = await fetch(`/api/global-cars/${currentGlobalCar.id}`, { method: "DELETE" });
        if (res.ok) {
            currentGlobalCar = null;
            await fetchGlobalCars();
            showToast("Car deleted from global library.");
        }
    } catch (err) {
        console.error("Error deleting global car:", err);
    }
}

async function saveGlobalCarClick() {
    if (!currentGlobalCar) return;
    const nameInput = document.getElementById("globalCarNameInput");
    if (!nameInput || nameInput.value.trim() === "") return;
    
    const payload = {
        name: nameInput.value.trim(),
        image_path: currentGlobalCar.image_path || ""
    };
    
    try {
        const res = await fetch(`/api/global-cars/${currentGlobalCar.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const prevId = currentGlobalCar.id;
            await fetchGlobalCars();
            selectGlobalCar(prevId);
            showToast("Car details updated!");
        }
    } catch (err) {
        console.error("Error saving global car:", err);
    }
}

async function handleGlobalCarImageUpload(e) {
    if (!currentGlobalCar) return;
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch(`/api/global-cars/${currentGlobalCar.id}/image`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            currentGlobalCar.image_path = data.image_path;
            updateGlobalCarImagePreview();
            showToast("Car image updated globally!");
        }
    } catch (err) {
        console.error("Error uploading global car image:", err);
    }
}

async function driveSetupClick(trackId, carSetupId) {
    // Switch to drive tab
    const driveTabBtn = document.querySelector('.nav-tab[data-tab="drive"]');
    if (driveTabBtn) driveTabBtn.click();
    
    // Set active track and car in main console view so the console updates
    selectTrack(trackId, carSetupId);
    
    // Pre-select track & car
    modalSelectedTrackId = trackId;
    modalSelectedCarSetupId = carSetupId;
    
    // Jump straight to step 3 (Options & Checklist)
    currentModalStep = 3;
    
    // Reset Xbox toggle state on open
    modalAutoEnableAutoDriveValue = false;
    const modalAutoDriveToggle = document.getElementById("modalAutoDriveToggle");
    if (modalAutoDriveToggle) {
        modalAutoDriveToggle.classList.remove("active");
        modalAutoDriveToggle.querySelector(".toggle-text").textContent = "Dont enable AutoDrive";
    }
    
    updateModalStepUI();
    
    const track = tracks.find(t => t.id === trackId);
    if (track) renderChecklistForModal(track);
    
    modalWarningText.textContent = "";
    checklistModal.classList.add("active");
}
window.driveSetupClick = driveSetupClick;

function switchGuideTopic(topicId) {
    // Hide all guide articles
    document.querySelectorAll(".guide-article").forEach(article => {
        article.style.display = "none";
    });
    // Show target article
    const target = document.getElementById(topicId);
    if (target) {
        target.style.display = "block";
    }
    
    // Update active class on left guide list items
    const guidePanel = document.getElementById("tab-guide");
    if (guidePanel) {
        guidePanel.querySelectorAll(".track-item").forEach(btn => {
            btn.classList.remove("active");
            if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(topicId)) {
                btn.classList.add("active");
            }
        });
    }
}
window.switchGuideTopic = switchGuideTopic;

