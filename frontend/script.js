// ============================================
// 1. ELEMENTS
// ============================================

const fileInput = document.getElementById('fileInput');
const fileNameDisplay = document.getElementById('fileName');
const uploadButton = document.getElementById('uploadButton');
const expiryTime = document.getElementById('expiryTime');
const maxAccesses = document.getElementById('maxAccesses');
const uploadStatus = document.getElementById('uploadStatus');

const recoverButton = document.getElementById('recoverButton');
const vaultIdInput = document.getElementById('vaultIdInput');
const recoveryStatus = document.getElementById('recoveryStatus');

const revokeButton = document.getElementById('revokeButton');
const revokeVaultId = document.getElementById('revokeVaultId');
const revokeStatus = document.getElementById('revokeStatus');

const historyButton = document.getElementById('historyButton');
const historyVaultId = document.getElementById('historyVaultId');
const historyStatus = document.getElementById('historyStatus');
const historyResults = document.getElementById('historyResults');


// ============================================
// 2. FILE SELECTION DISPLAY
// ============================================

fileInput.addEventListener('change', function () {

    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = fileInput.files[0].name;
    } else {
        fileNameDisplay.textContent = 'No file selected';
    }

});


// ============================================
// 3. FILE UPLOAD
// ============================================

uploadButton.addEventListener('click', async function () {

    if (fileInput.files.length === 0) {
        uploadStatus.textContent = 'Please select a file first!';
        return;
    }

    const file = fileInput.files[0];
    const expiry = expiryTime.value;
    const accessLimit = Number(maxAccesses.value);

    if (!Number.isInteger(accessLimit) ||
        accessLimit < 1 ||
        accessLimit > 100) {

        uploadStatus.textContent =
            'Maximum accesses must be between 1 and 100.';
        return;
    }

    const formData = new FormData();

    formData.append('file', file);
    formData.append('expiry_minutes', expiry);
    formData.append('max_accesses', accessLimit);

    uploadButton.disabled = true;
    uploadButton.textContent = 'Encrypting...';
    uploadStatus.textContent = 'Uploading and encrypting your file...';

    try {

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }

        uploadStatus.textContent =
            'File secured successfully! Vault ID: ' + result.vault_id;

        // Automatically fill Vault ID fields
        vaultIdInput.value = result.vault_id;
        revokeVaultId.value = result.vault_id;
        historyVaultId.value = result.vault_id;

        console.log('Upload Result:', result);

        fileInput.value = '';
        fileNameDisplay.textContent = 'No file selected';

    } catch (error) {

        uploadStatus.textContent = 'Error: ' + error.message;
        console.error('Upload Error:', error);

    } finally {

        uploadButton.disabled = false;
        uploadButton.textContent = 'Encrypt & Upload';

    }

});


// ============================================
// 4. RECOVER FILE
// ============================================

recoverButton.addEventListener('click', async function () {

    const vaultId = vaultIdInput.value.trim();

    if (!vaultId) {
        recoveryStatus.textContent = 'Please enter your Vault ID.';
        return;
    }

    recoverButton.disabled = true;
    recoveryStatus.textContent = 'Recovering your file...';

    try {

        const response = await fetch(
            `/api/recover/${encodeURIComponent(vaultId)}`
        );

        if (!response.ok) {

            const result = await response.json();
            throw new Error(result.error || 'Recovery failed');

        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = 'recovered-file';

        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);

        recoveryStatus.textContent = 'File recovered successfully!';

    } catch (error) {

        recoveryStatus.textContent = 'Error: ' + error.message;

    } finally {

        recoverButton.disabled = false;

    }

});


// ============================================
// 5. REVOKE FILE ACCESS
// ============================================

revokeButton.addEventListener('click', async function () {

    const vaultId = revokeVaultId.value.trim();

    if (!vaultId) {
        revokeStatus.textContent = 'Please enter your Vault ID.';
        return;
    }

    revokeButton.disabled = true;
    revokeStatus.textContent = 'Revoking access...';

    try {

        const response = await fetch(
            `/api/revoke/${encodeURIComponent(vaultId)}`,
            { method: 'POST' }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Revoke failed');
        }

        revokeStatus.textContent = 'Vault access revoked successfully!';

    } catch (error) {

        revokeStatus.textContent = 'Error: ' + error.message;

    } finally {

        revokeButton.disabled = false;

    }

});


// ============================================
// 6. ACCESS HISTORY
// ============================================

historyButton.addEventListener('click', async function () {

    const vaultId = historyVaultId.value.trim();

    if (!vaultId) {
        historyStatus.textContent = 'Please enter your Vault ID.';
        historyResults.replaceChildren();
        return;
    }

    historyButton.disabled = true;
    historyStatus.textContent = 'Loading access history...';
    historyResults.replaceChildren();

    try {

        const response = await fetch(
            `/api/history/${encodeURIComponent(vaultId)}`
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Could not load history');
        }

        historyResults.replaceChildren();

        if (!result.history || result.history.length === 0) {
            historyStatus.textContent = 'No activity found.';
            return;
        }

        historyStatus.textContent =
            `${result.history.length} activity event(s) found.`;

        result.history.forEach(event => {

            const item = document.createElement('div');
            item.className = 'history-item';

            const action = document.createElement('h4');
            action.textContent = event.action;

            const time = document.createElement('p');
            time.textContent = new Date(event.access_time).toLocaleString();

            item.appendChild(action);
            item.appendChild(time);

            historyResults.appendChild(item);

        });

    } catch (error) {

        historyStatus.textContent = 'Error: ' + error.message;

    } finally {

        historyButton.disabled = false;

    }

});


// ============================================
// 7. SMOOTH SCROLL NAVIGATION
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(link => {

    link.addEventListener('click', function (e) {

        const targetId = this.getAttribute('href');

        if (targetId === '#') {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        const targetSection = document.querySelector(targetId);

        if (targetSection) {

            e.preventDefault();

            targetSection.scrollIntoView({
                behavior: 'smooth'
            });

        }

    });

});