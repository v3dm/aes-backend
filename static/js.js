// const baseURL = '';
// function togglePassword(id, btn) {
//   const input = document.getElementById(id);
//   if (input.type === "password") {
//     input.type = "text";
//     btn.textContent = "🙈"; // change icon to hide mode
//   } else {
//     input.type = "password";
//     btn.textContent = "👁️"; // change icon back
//   }
// }

//   async function doEncrypt() {
//   const plaintext = document.getElementById('plaintext').value;
//   const password = document.getElementById('password').value;
//   if (!password) { alert("Enter a password"); return; }

//   // use baseURL so we call your Render backend (not relative origin)
//   const resp = await fetch(baseURL + '/api/encrypt', {
//     method: 'POST',
//     headers: {'Content-Type': 'application/json'},
//     body: JSON.stringify({ plaintext, password })
//   });
//   if (!resp.ok) {
//     alert('Encryption failed: ' + (await resp.text()));
//     return;
//   }
//   const data = await resp.json();
//   const ciphertext_b64 = data.ciphertext_b64;

//   // update UI
//   document.getElementById('ciphertext').value = ciphertext_b64;
//   document.getElementById('ciphertext_in').value = ciphertext_b64; // helpful copy

//   // debug log so we can see in Console the save step
//   console.log("Encrypt succeeded — ciphertext length:", ciphertext_b64.length);

//   // --- auto-save to DB (only ciphertext, no password) ---
//   const filename = document.getElementById('filenameInput')?.value || null;
//   const note = document.getElementById('noteInput')?.value || "auto-saved";

//   const autoSaveEnabled = (document.getElementById('autoSaveToggle')?.checked ?? true);

//   if (autoSaveEnabled) {
//     console.log("Calling saveCiphertext...");
//     saveCiphertext(ciphertext_b64, filename, note).then(res => {
//       if (res) {
//         console.log("Saved record id:", res.id);
//       } else {
//         console.log("Save returned null or failed.");
//       }
//     });
//   } else {
//     console.log("Auto-save disabled by user.");
//   }
// }


//     async function doDecrypt() {
//       const ciphertext_b64 = document.getElementById('ciphertext_in').value;
//       const password = document.getElementById('password_in').value;
//       if (!ciphertext_b64 || !password) { alert("Provide ciphertext and password"); return; }

//       const resp = await fetch('/api/decrypt', {
//         method: 'POST',
//         headers: {'Content-Type': 'application/json'},
//         body: JSON.stringify({ ciphertext_b64, password })
//       });
//       if (!resp.ok) {
//         const j = await resp.json().catch(()=>null);
//         alert('Decryption failed: ' + (j?.detail || await resp.text()));
//         return;
//       }
//       const data = await resp.json();
//       document.getElementById('recovered').value = data.plaintext;
//     }


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// js.js
// Use same-origin by default. If your backend runs elsewhere, set baseURL to that URL.
const baseURL = '';

// toggle password visibility (optional)
function togglePassword(id, btn) {
  const input = document.getElementById(id);
  if (!input) return;
  if (input.type === "password") {
    input.type = "text";
    if (btn) btn.textContent = "🙈";
  } else {
    input.type = "password";
    if (btn) btn.textContent = "👁️";
  }
}

async function doEncrypt() {
  const plaintext = document.getElementById('plaintext').value;
  const password = document.getElementById('password').value;
  if (!password) { alert("Enter a password"); return; }

  const resp = await fetch(baseURL + '/api/encrypt', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ plaintext, password })
  });
  if (!resp.ok) {
    alert('Encryption failed: ' + (await resp.text()));
    return;
  }
  const data = await resp.json();
  const ciphertext_b64 = data.ciphertext_b64;

  // update UI
  document.getElementById('ciphertext').value = ciphertext_b64;
  document.getElementById('ciphertext_in').value = ciphertext_b64; // helpful copy

  console.log("Encrypt succeeded — ciphertext length:", ciphertext_b64.length);

  // --- auto-save to DB (only ciphertext, no password) ---
  const filename = document.getElementById('filenameInput')?.value || null;
  const note = document.getElementById('noteInput')?.value || "auto-saved";

  const autoSaveEnabled = (document.getElementById('autoSaveToggle')?.checked ?? true);

  if (autoSaveEnabled) {
    console.log("Calling saveCiphertext...");
    saveCiphertext(ciphertext_b64, filename, note).then(res => {
      if (res) {
        console.log("Saved record id:", res.id);
      } else {
        console.log("Save returned null or failed.");
      }
    });
  } else {
    console.log("Auto-save disabled by user.");
  }
}

async function doDecrypt() {
  const ciphertext_b64 = document.getElementById('ciphertext_in').value;
  const password = document.getElementById('password_in').value;
  if (!ciphertext_b64 || !password) { alert("Provide ciphertext and password"); return; }

  const resp = await fetch(baseURL + '/api/decrypt', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ ciphertext_b64, password })
  });
  if (!resp.ok) {
    const j = await resp.json().catch(()=>null);
    alert('Decryption failed: ' + (j?.detail || await resp.text()));
    return;
  }
  const data = await resp.json();
  document.getElementById('recovered').value = data.plaintext;
}

// Save ciphertext metadata to server (calls your /api/save endpoint)
async function saveCiphertext(ciphertext_b64, filename=null, note=null, owner=null) {
  try {
    const resp = await fetch(baseURL + '/api/save', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ ciphertext_b64, filename, note, owner })
    });
    if (!resp.ok) {
      const txt = await resp.text().catch(()=>null);
      console.warn('saveCiphertext failed', resp.status, txt);
      return null;
    }
    return await resp.json();
  } catch (e) {
    console.error('saveCiphertext exception', e);
    return null;
  }
}
