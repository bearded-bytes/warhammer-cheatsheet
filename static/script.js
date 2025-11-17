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
            // Show result
            displayResult(data);
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
