// Handle form submission
document.getElementById('cheatSheetForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Get form data
    const formData = new FormData(this);

    // Show loading, hide errors and results
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'none';

    try {
        // Submit to server
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Hide loading
        document.getElementById('loading').style.display = 'none';

        if (response.ok && data.success) {
            // Check if we need to show leader selection UI
            if (data.requires_attachment_selection) {
                showLeaderSelection(data, formData);
            } else {
                // Show result directly
                displayResult(data);
            }
        } else {
            // Show error
            showError(data.error || 'An error occurred while generating the cheat sheet');
        }
    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        showError('Network error: ' + error.message);
    }
});

function displayResult(data) {
    // Update army info
    document.getElementById('armyName').textContent = `${data.army_name} (${data.faction})`;
    document.getElementById('armyPoints').textContent = `${data.points} Points`;

    // Display the cheat sheet
    const preview = document.getElementById('cheatSheetPreview');

    if (data.format === 'html') {
        // For HTML, create an iframe to display it properly
        preview.innerHTML = data.content;
    } else {
        // For Markdown, display as pre-formatted text
        preview.innerHTML = `<pre>${escapeHtml(data.content)}</pre>`;
    }

    // Store the content for download
    window.currentCheatSheet = {
        content: data.content,
        format: data.format,
        armyName: data.army_name
    };

    // Show result container
    document.getElementById('result').style.display = 'block';

    // Scroll to result
    document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}

function downloadCheatSheet() {
    if (!window.currentCheatSheet) return;

    const { content, format, armyName } = window.currentCheatSheet;
    const filename = `${sanitizeFilename(armyName)}_cheatsheet.${format}`;

    // Create blob and download
    const blob = new Blob([content], {
        type: format === 'html' ? 'text/html' : 'text/markdown'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function printCheatSheet() {
    if (!window.currentCheatSheet) return;

    const { content, format } = window.currentCheatSheet;

    if (format === 'html') {
        // Open in new window and print
        const printWindow = window.open('', '_blank');
        printWindow.document.write(content);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
        }, 250);
    } else {
        alert('Print is only available for HTML format. Please generate as HTML to print.');
    }
}

function resetForm() {
    document.getElementById('cheatSheetForm').reset();
    document.getElementById('result').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    window.currentCheatSheet = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function sanitizeFilename(name) {
    return name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Leader selection functionality
function showLeaderSelection(data, originalFormData) {
    // Hide the form
    document.getElementById('cheatSheetForm').style.display = 'none';

    // Create leader selection UI
    const selectionDiv = document.getElementById('leaderSelection') || createLeaderSelectionDiv();
    selectionDiv.style.display = 'block';

    // Build unit counts (for handling duplicates)
    const unitCounts = {};
    data.available_units.forEach(unit => {
        unitCounts[unit.name] = (unitCounts[unit.name] || 0) + 1;
    });

    // Build leader selection HTML
    let html = `
        <h2>Configure Leader Attachments</h2>
        <p>Select which units each leader should attach to:</p>
        <div class="leader-cards">
    `;

    data.leaders_data.forEach((leader, leaderIdx) => {
        html += `
            <div class="leader-card">
                <h3>${escapeHtml(leader.name)}</h3>
                <label>Attach to:</label>
                <select id="leader_${leaderIdx}" class="leader-select" data-leader-name="${escapeHtml(leader.name)}">
                    <option value="">-- None (unattached) --</option>
        `;

        // Add options for attachable units
        leader.attachable_units.forEach(attachable => {
            // Find matching units in the army
            const matchingUnits = data.available_units.filter(u => u.name === attachable);
            matchingUnits.forEach((unit, idx) => {
                const suffix = matchingUnits.length > 1 ? ` #${idx + 1}` : '';
                const value = matchingUnits.length > 1 ? `${unit.name} #${idx + 1}` : unit.name;
                html += `<option value="${escapeHtml(value)}">${escapeHtml(unit.name)}${suffix}</option>`;
            });
        });

        html += `
                </select>
            </div>
        `;
    });

    html += `
        </div>
        <div class="button-group" style="margin-top: 20px;">
            <button onclick="submitAttachments()" class="btn-primary">Generate Final Cheat Sheet</button>
            <button onclick="cancelLeaderSelection()" class="btn-secondary">Cancel</button>
        </div>
    `;

    selectionDiv.innerHTML = html;

    // Store data for later use
    window.leaderSelectionData = {
        originalData: data,
        originalFormData: originalFormData
    };

    // Add change listeners to track claimed units
    document.querySelectorAll('.leader-select').forEach(select => {
        select.addEventListener('change', updateAvailableUnits);
    });
}

function createLeaderSelectionDiv() {
    const div = document.createElement('div');
    div.id = 'leaderSelection';
    div.className = 'leader-selection-container';
    div.style.display = 'none';
    document.querySelector('.main-content').appendChild(div);
    return div;
}

function updateAvailableUnits() {
    // Track which units are currently claimed
    const claimed = new Set();
    document.querySelectorAll('.leader-select').forEach(select => {
        if (select.value) {
            claimed.add(select.value);
        }
    });

    // Update all selects to disable claimed options
    document.querySelectorAll('.leader-select').forEach(select => {
        const currentValue = select.value;
        Array.from(select.options).forEach(option => {
            if (option.value && option.value !== currentValue && claimed.has(option.value)) {
                option.disabled = true;
                option.style.color = '#999';
            } else {
                option.disabled = false;
                option.style.color = '';
            }
        });
    });
}

async function submitAttachments() {
    const data = window.leaderSelectionData;
    if (!data) return;

    // Collect attachment selections
    const attachments = {};
    document.querySelectorAll('.leader-select').forEach(select => {
        const leaderName = select.getAttribute('data-leader-name');
        const unitName = select.value;
        if (unitName) {
            attachments[leaderName] = unitName;
        }
    });

    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('leaderSelection').style.display = 'none';

    try {
        // Get original army list text
        const armyListText = data.originalFormData.get('army_list');
        const format = data.originalFormData.get('format');

        // Submit to new endpoint with attachments
        const response = await fetch('/generate_with_attachments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                army_list: armyListText,
                format: format,
                attachments: attachments
            })
        });

        const result = await response.json();

        // Hide loading
        document.getElementById('loading').style.display = 'none';

        if (response.ok && result.success) {
            displayResult(result);
        } else {
            showError(result.error || 'Error generating cheat sheet with attachments');
        }
    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        showError('Network error: ' + error.message);
    }
}

function cancelLeaderSelection() {
    document.getElementById('leaderSelection').style.display = 'none';
    document.getElementById('cheatSheetForm').style.display = 'block';
    window.leaderSelectionData = null;
}

// Add example army list button functionality
function loadExample() {
    const exampleList = `DG MORTAL WOUNDS (2000 Points)

Death Guard
Death Lord's Chosen
Strike Force (2,000 Points)

CHARACTERS

Mortarion (380 Points)
  • Warlord
  • 1x Lantern
  • 1x Rotwind
  • 1x Silence

Lord of Contagion (150 Points)
  • 1x Manreaper
  • Enhancements: Warprot Talisman

BATTLELINE

Plague Marines (95 Points)
  • 1x Plague Champion
     ◦ 1x Plasma gun
     ◦ 1x Power fist
  • 4x Plague Marine
     ◦ 1x Blight launcher
     ◦ 1x Boltgun
     ◦ 4x Plague knives
`;

    document.getElementById('army_list').value = exampleList;
}
