// Generative AI Sales Agent - Call Simulator Javascript Engine

let activeCallSid = null;
let isCallActive = false;
let isSpeaking = false;
let callDurationSeconds = 0;
let timerInterval = null;
let synthesisVoice = null;
let recognition = null;
let ttsEnabled = true;

// DOM Elements
const startSimBtn = document.getElementById('startSimBtn');
const triggerRealCallBtn = document.getElementById('triggerRealCallBtn');
const endCallBtn = document.getElementById('endCallBtn');
const ttsToggle = document.getElementById('ttsToggle');
const micBtn = document.getElementById('micBtn');
const sendBtn = document.getElementById('sendBtn');
const chatInput = document.getElementById('chatInput');
const chatTranscript = document.getElementById('chatTranscript');
const callDuration = document.getElementById('callDuration');
const phoneCallStatus = document.getElementById('phoneCallStatus');
const phoneCallView = document.getElementById('phoneCallView');
const phoneOverlay = document.getElementById('phoneOverlay');
const phoneSetupForm = document.getElementById('phoneSetupForm');
const studentNameInput = document.getElementById('studentName');
const studentPhoneInput = document.getElementById('phone');
const waveformContainer = document.getElementById('waveformContainer');
const speechHint = document.getElementById('speechHint');

// Inspector Elements
const stateStage = document.getElementById('stateStage');
const stateCourse = document.getElementById('stateCourse');
const stateDate = document.getElementById('stateDate');
const stateTime = document.getElementById('stateTime');
const stateName = document.getElementById('stateName');
const stateMobile = document.getElementById('stateMobile');
const stateSessionId = document.getElementById('stateSessionId');

// Initialize Web Speech APIs
function initSpeech() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      synthesisVoice = getVoiceForSelection();
    };
    synthesisVoice = getVoiceForSelection();
  } else {
    console.warn("Speech Synthesis (TTS) is not supported in this browser.");
    if (ttsToggle) ttsToggle.style.display = 'none';
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    const langSelect = document.getElementById('callLanguage');
    recognition.lang = langSelect ? langSelect.value : 'te-IN';

    recognition.onstart = () => {
      micBtn.classList.add('recording');
      speechHint.textContent = "Listening to you... Speak now!";
    };

    recognition.onresult = (event) => {
      const resultText = event.results[0][0].transcript;
      chatInput.value = resultText;
      speechHint.textContent = `Heard: "${resultText}"`;
      submitStudentTurn();
    };

    recognition.onerror = (event) => {
      console.error("Speech Recognition Error:", event.error);
      micBtn.classList.remove('recording');
      if (event.error === 'not-allowed') {
        speechHint.textContent = "Microphone access blocked. Click mic to retry.";
      } else {
        speechHint.textContent = "Speech recognition failed. Try typing instead.";
      }
    };

    recognition.onend = () => {
      micBtn.classList.remove('recording');
      if (speechHint.textContent.startsWith("Listening")) {
        speechHint.textContent = "Microphone closed.";
      }
    };
  } else {
    console.warn("Speech Recognition (STT) is not supported in this browser.");
    if (micBtn) micBtn.style.display = 'none';
  }
}

function getVoiceForSelection() {
  const langSelect = document.getElementById('callLanguage');
  const genderSelect = document.getElementById('voiceGender');
  const selectedLang = langSelect ? langSelect.value : 'te-IN';
  const selectedGender = genderSelect ? genderSelect.value : 'female';
  
  if (!('speechSynthesis' in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  
  const langPrefix = selectedLang.substring(0, 2).toLowerCase();
  let filtered = voices.filter(v => v.lang.toLowerCase().replace('_', '-').startsWith(langPrefix));
  if (filtered.length === 0) {
    filtered = voices;
  }
  
  const maleKeywords = ['male', 'david', 'mark', 'george', 'ravi', 'harsh', 'charlie', 'guy', 'enrique', 'miguel', 'standard-b', 'zayd', 'chanakya'];
  const femaleKeywords = ['female', 'zira', 'hazel', 'aditi', 'heera', 'raveena', 'kajal', 'conchita', 'lucia', 'standard-a', 'google', 'microsoft'];
  
  let voice = null;
  if (selectedGender === 'male') {
    voice = filtered.find(v => maleKeywords.some(kw => v.name.toLowerCase().includes(kw)));
  } else {
    voice = filtered.find(v => femaleKeywords.some(kw => v.name.toLowerCase().includes(kw)));
  }
  
  if (!voice) {
    if (selectedGender === 'male') {
      voice = filtered.find(v => !femaleKeywords.some(kw => v.name.toLowerCase().includes(kw)));
    } else {
      voice = filtered.find(v => !maleKeywords.some(kw => v.name.toLowerCase().includes(kw)));
    }
  }
  
  if (!voice && filtered.length > 0) {
    voice = filtered[0];
  }
  return voice;
}

let currentSpeechAudio = null;
let isPlayQueueActive = false;
let currentPlayQueueIndex = 0;

function chunkText(text, maxLen = 160) {
  if (!text) return [];
  
  const sentences = text.split(/([.!?;\n।]+)/);
  const chunks = [];
  let currentChunk = "";
  
  for (let i = 0; i < sentences.length; i++) {
    const part = sentences[i];
    if (part === undefined || part === null) continue;
    
    if (/^[.!?;\n।]+$/.test(part)) {
      currentChunk += part;
      continue;
    }
    
    if (currentChunk && (currentChunk.length + part.length > maxLen)) {
      chunks.push(currentChunk.trim());
      currentChunk = part;
    } else {
      currentChunk += part;
    }
  }
  
  if (currentChunk.trim()) {
    chunks.push(currentChunk.trim());
  }
  
  const finalChunks = [];
  for (const chunk of chunks) {
    if (chunk.length <= maxLen) {
      finalChunks.push(chunk);
    } else {
      const words = chunk.split(/([,\s]+)/);
      let subChunk = "";
      for (const word of words) {
        if (subChunk.length + word.length > maxLen) {
          if (subChunk.trim()) finalChunks.push(subChunk.trim());
          subChunk = word;
        } else {
          subChunk += word;
        }
      }
      if (subChunk.trim()) {
        finalChunks.push(subChunk.trim());
      }
    }
  }
  
  return finalChunks.filter(c => c.trim().length > 0);
}

function fallbackSpeakText(text, callback) {
  if (!('speechSynthesis' in window)) {
    if (callback) callback();
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  if (synthesisVoice) {
    utterance.voice = synthesisVoice;
  }
  utterance.rate = 0.95;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    isSpeaking = true;
    if (waveformContainer) waveformContainer.classList.add('active');
  };

  utterance.onend = () => {
    isSpeaking = false;
    if (waveformContainer) waveformContainer.classList.remove('active');
    if (callback) callback();
  };

  utterance.onerror = (e) => {
    console.error("Synthesis fallback error:", e);
    isSpeaking = false;
    if (waveformContainer) waveformContainer.classList.remove('active');
    if (callback) callback();
  };

  window.speechSynthesis.speak(utterance);
}

function speakText(text, callback) {
  if (!ttsEnabled) {
    if (callback) callback();
    return;
  }

  isPlayQueueActive = false;

  if (currentSpeechAudio) {
    currentSpeechAudio.pause();
    currentSpeechAudio = null;
  }
  
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }

  const langSelect = document.getElementById('callLanguage');
  const selectedLang = langSelect ? langSelect.value : 'te-IN';

  const chunks = chunkText(text, 150);
  if (chunks.length === 0) {
    if (callback) callback();
    return;
  }

  isPlayQueueActive = true;
  currentPlayQueueIndex = 0;

  function playNextChunk() {
    if (!isPlayQueueActive) {
      isSpeaking = false;
      if (waveformContainer) waveformContainer.classList.remove('active');
      return;
    }

    if (currentPlayQueueIndex >= chunks.length) {
      isPlayQueueActive = false;
      isSpeaking = false;
      if (waveformContainer) waveformContainer.classList.remove('active');
      if (callback) callback();
      return;
    }

    const chunkTextStr = chunks[currentPlayQueueIndex];
    currentPlayQueueIndex++;

    isSpeaking = true;
    if (waveformContainer) waveformContainer.classList.add('active');

    const ttsUrl = `/api/tts?lang=${encodeURIComponent(selectedLang)}&text=${encodeURIComponent(chunkTextStr)}`;
    const audio = new Audio(ttsUrl);
    currentSpeechAudio = audio;

    audio.onended = () => {
      if (currentSpeechAudio === audio) {
        currentSpeechAudio = null;
      }
      playNextChunk();
    };

    audio.onerror = (e) => {
      console.warn("Proxy TTS failed, trying browser fallback SpeechSynthesis...", e);
      if (currentSpeechAudio === audio) {
        currentSpeechAudio = null;
      }
      fallbackSpeakText(chunkTextStr, () => {
        playNextChunk();
      });
    };

    audio.play().catch(err => {
      console.warn("Proxy TTS play blocked, trying browser fallback SpeechSynthesis...", err);
      if (currentSpeechAudio === audio) {
        currentSpeechAudio = null;
      }
      fallbackSpeakText(chunkTextStr, () => {
        playNextChunk();
      });
    });
  }

  playNextChunk();
}

function parseTwiML(xmlText) {
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, "text/xml");
    
    const parserError = xmlDoc.getElementsByTagName("parsererror");
    if (parserError.length > 0) {
      throw new Error("XML Parsing error");
    }

    const sayNodes = xmlDoc.getElementsByTagName("Say");
    let speechText = "";
    for (let i = 0; i < sayNodes.length; i++) {
      speechText += sayNodes[i].textContent + " ";
    }

    const hasGather = xmlDoc.getElementsByTagName("Gather").length > 0;
    const hasHangup = xmlDoc.getElementsByTagName("Hangup").length > 0;

    return {
      speechText: speechText.trim(),
      shouldHangup: hasHangup || !hasGather
    };
  } catch (err) {
    console.error("TwiML parsing failed:", err);
    const sayMatch = xmlText.match(/<Say[^>]*>([\s\S]*?)<\/Say>/i);
    const speech = sayMatch ? sayMatch[1].replace(/<[^>]*>/g, '') : "Call connected.";
    const hasHangup = xmlText.includes("<Hangup");
    return {
      speechText: speech.trim(),
      shouldHangup: hasHangup
    };
  }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

async function startSimulatedCall() {
  const studentPhone = studentPhoneInput.value.trim();
  const studentName = studentNameInput.value.trim();

  if (!studentPhone) {
    alert("Please enter a phone number!");
    return;
  }

  const langSelect = document.getElementById('callLanguage');
  const genderSelect = document.getElementById('voiceGender');
  const selectedLang = langSelect ? langSelect.value : 'te-IN';
  const selectedGender = genderSelect ? genderSelect.value : 'female';

  if (recognition) {
    recognition.lang = selectedLang;
  }
  synthesisVoice = getVoiceForSelection();

  activeCallSid = `SIM-${Date.now()}`;
  isCallActive = true;
  callDurationSeconds = 0;
  callDuration.textContent = "00:00";
  chatTranscript.innerHTML = "";
  
  phoneCallStatus.textContent = "Ringing...";
  phoneSetupForm.style.display = "none";
  startSimBtn.style.display = "none";
  triggerRealCallBtn.style.display = "none";
  
  await new Promise(resolve => setTimeout(resolve, 1500));

  phoneOverlay.style.display = "none";
  phoneCallView.style.display = "flex";
  
  timerInterval = setInterval(() => {
    callDurationSeconds++;
    callDuration.textContent = formatTime(callDurationSeconds);
  }, 1000);

  addTranscriptMessage("system", `Call connected with Rocky AI Developer (${selectedLang.toUpperCase()} - ${selectedGender.toUpperCase()})...`);
  updateStateInspector(activeCallSid);

  try {
    const formData = new URLSearchParams();
    formData.append("CallSid", activeCallSid);
    formData.append("From", studentPhone);
    formData.append("To", "+14155552345");
    formData.append("Language", selectedLang);
    formData.append("Gender", selectedGender);

    const response = await fetch('/voice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    });

    if (!response.ok) throw new Error("Could not initialize call audio.");

    const twimlText = await response.text();
    const result = parseTwiML(twimlText);

    addTranscriptMessage("agent", result.speechText);
    speakText(result.speechText, () => {
      unlockInput(true);
    });

    if (result.shouldHangup) {
      setTimeout(endCall, 5000);
    }
  } catch (err) {
    addTranscriptMessage("system", `Call connection error: ${err.message}`);
    setTimeout(endCall, 3000);
  }
}

async function submitStudentTurn() {
  const text = chatInput.value.trim();
  if (!text || !isCallActive) return;

  chatInput.value = "";
  unlockInput(false);

  addTranscriptMessage("student", text);

  const studentPhone = studentPhoneInput.value.trim();
  const langSelect = document.getElementById('callLanguage');
  const genderSelect = document.getElementById('voiceGender');
  const selectedLang = langSelect ? langSelect.value : 'te-IN';
  const selectedGender = genderSelect ? genderSelect.value : 'female';

  try {
    const formData = new URLSearchParams();
    formData.append("CallSid", activeCallSid);
    formData.append("From", studentPhone);
    formData.append("SpeechResult", text);
    formData.append("Language", selectedLang);
    formData.append("Gender", selectedGender);

    const response = await fetch('/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    });

    if (!response.ok) throw new Error("Server responded with error.");

    const twimlText = await response.text();
    const result = parseTwiML(twimlText);

    addTranscriptMessage("agent", result.speechText);
    
    updateStateInspector(activeCallSid);

    speakText(result.speechText, () => {
      if (result.shouldHangup) {
        addTranscriptMessage("system", "Agent hung up. Call ended.");
        setTimeout(endCall, 2000);
      } else {
        unlockInput(true);
      }
    });

  } catch (err) {
    addTranscriptMessage("system", `Error: ${err.message}`);
    unlockInput(true);
  }
}

function endCall() {
  isCallActive = false;
  activeCallSid = null;
  isPlayQueueActive = false;
  
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  
  if (currentSpeechAudio) {
    currentSpeechAudio.pause();
    currentSpeechAudio = null;
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  
  if (waveformContainer) waveformContainer.classList.remove('active');
  unlockInput(false);

  phoneCallView.style.display = "none";
  phoneOverlay.style.display = "flex";
  phoneSetupForm.style.display = "block";
  startSimBtn.style.display = "inline-flex";
  triggerRealCallBtn.style.display = "inline-flex";
  phoneCallStatus.textContent = "Call Ended";
  
  resetStateInspector();
}

function unlockInput(enable) {
  chatInput.disabled = !enable;
  sendBtn.disabled = !enable;
  if (enable) {
    chatInput.focus();
    speechHint.textContent = "Type your response or click the microphone.";
  } else {
    speechHint.textContent = "Rocky is speaking...";
  }
}

// Security note: Sanitize output dynamically when inserting messages to chat transcript
function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

function addTranscriptMessage(sender, text) {
  const bubble = document.createElement('div');
  bubble.classList.add('chat-bubble');

  const escapedText = escapeHTML(text);

  if (sender === "agent") {
    bubble.classList.add('bubble-agent');
    bubble.innerHTML = `<strong>Rocky AI Developer:</strong> ${escapedText}`;
  } else if (sender === "student") {
    bubble.classList.add('bubble-student');
    bubble.innerHTML = `<strong>You:</strong> ${escapedText}`;
  } else {
    bubble.classList.add('bubble-info');
    bubble.textContent = text; // textContent is safe by default
  }

  chatTranscript.appendChild(bubble);
  chatTranscript.scrollTop = chatTranscript.scrollHeight;
}

async function updateStateInspector(callId) {
  if (!callId) return;

  try {
    const response = await fetch(`/api/state/${callId}?_t=${Date.now()}`);
    if (response.ok) {
      const state = await response.json();
      
      stateStage.textContent = state.stage || "-";
      stateCourse.textContent = state.course_selected || "-";
      stateDate.textContent = state.demo_date || "-";
      stateTime.textContent = state.demo_time || "-";
      stateName.textContent = state.student_name || "-";
      stateMobile.textContent = state.student_mobile || "-";
      stateSessionId.textContent = callId;

      document.querySelectorAll('.step-item').forEach(step => {
        const stepStage = step.getAttribute('data-stage');
        step.classList.remove('active', 'completed');
        
        if (stepStage === state.stage) {
          step.classList.add('active');
        } else if (isStageCompleted(stepStage, state.stage)) {
          step.classList.add('completed');
        }
      });
    }
  } catch (err) {
    console.error("Failed to load call state details:", err);
  }
}

const STAGE_ORDER = ["intro", "course_selection", "demo_interest", "demo_date_selection", "demo_time_selection", "collect_student_details", "booking_complete"];
function isStageCompleted(checkedStage, currentStage) {
  const checkedIndex = STAGE_ORDER.indexOf(checkedStage);
  const currentIndex = STAGE_ORDER.indexOf(currentStage);
  return checkedIndex !== -1 && currentIndex !== -1 && checkedIndex < currentIndex;
}

function resetStateInspector() {
  stateStage.textContent = "-";
  stateCourse.textContent = "-";
  stateDate.textContent = "-";
  stateTime.textContent = "-";
  stateName.textContent = "-";
  stateMobile.textContent = "-";
  stateSessionId.textContent = "-";
  
  document.querySelectorAll('.step-item').forEach(step => {
    step.classList.remove('active', 'completed');
  });
}

async function triggerRealTwilioCall() {
  const phone = studentPhoneInput.value.trim();
  if (!phone) {
    alert("Please enter a phone number to place a call!");
    return;
  }

  const langSelect = document.getElementById('callLanguage');
  const genderSelect = document.getElementById('voiceGender');
  const selectedLang = langSelect ? langSelect.value : 'te-IN';
  const selectedGender = genderSelect ? genderSelect.value : 'female';

  phoneCallStatus.textContent = "Triggering Twilio...";

  try {
    const response = await fetch('/trigger_call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, language: selectedLang, gender: selectedGender })
    });

    const data = await response.json();
    if (response.ok) {
      if (data.status === "started") {
        phoneCallStatus.textContent = "Outbound Call Started!";
        alert(`Twilio call started successfully! SID: ${data.call_sid}`);
      } else if (data.status === "simulated") {
        phoneCallStatus.textContent = "Simulated Call Successful";
        alert(`Simulated webhook triggered (Mode: Simulate).`);
      }
    } else {
      phoneCallStatus.textContent = "Twilio Failed";
      alert(`Twilio trigger failed: ${data.error || "Unknown error"}`);
    }
  } catch (err) {
    phoneCallStatus.textContent = "Network Error";
    alert(`Failed to trigger real call: ${err.message}`);
  } finally {
    setTimeout(() => {
      phoneCallStatus.textContent = "Idle";
    }, 4000);
  }
}

function setupEvents() {
  startSimBtn.addEventListener('click', startSimulatedCall);
  triggerRealCallBtn.addEventListener('click', triggerRealTwilioCall);
  endCallBtn.addEventListener('click', endCall);
  
  ttsToggle.addEventListener('click', () => {
    ttsEnabled = !ttsEnabled;
    ttsToggle.classList.toggle('active', ttsEnabled);
    if (!ttsEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      if (waveformContainer) waveformContainer.classList.remove('active');
    }
  });

  micBtn.addEventListener('click', () => {
    if (!recognition) {
      alert("Speech Recognition not supported in this browser. Please use Chrome/Edge or type your reply.");
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      isSpeaking = false;
      if (waveformContainer) waveformContainer.classList.remove('active');
    }
    try {
      recognition.start();
    } catch (e) {
      recognition.stop();
    }
  });

  sendBtn.addEventListener('click', submitStudentTurn);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      submitStudentTurn();
    }
  });

  const callLanguageSelect = document.getElementById('callLanguage');
  if (callLanguageSelect) {
    callLanguageSelect.addEventListener('change', () => {
      if (recognition) {
        recognition.lang = callLanguageSelect.value;
      }
      synthesisVoice = getVoiceForSelection();
    });
  }

  const voiceGenderSelect = document.getElementById('voiceGender');
  if (voiceGenderSelect) {
    voiceGenderSelect.addEventListener('change', () => {
      synthesisVoice = getVoiceForSelection();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initSpeech();
  setupEvents();
  resetStateInspector();
});
