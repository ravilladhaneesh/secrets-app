// Toggle visibility of the "Add Secret" form
function toggleNoteForm() {
    var formDiv = document.getElementById("add-note");
    var tableDiv = document.getElementById("notes-table");
    
    if (formDiv.style.display === "none" || formDiv.style.display === "") {
        formDiv.style.display = "block";  // Show the form
        tableDiv.style.display = "none";  // Hide the table
    } else {
        formDiv.style.display = "none";  // Hide the form
        tableDiv.style.display = "block";  // Show the table
    }
}

// Cancel the "Add Secret" form and show the table again
function cancelNoteForm() {
    document.getElementById("add-note").style.display = "none";
    document.getElementById("notes-table").style.display = "block";  // Show the notes table
}


function addReceivers() {
    const container = document.getElementById("receivers-fields");
    const index = findFirstMissingReceiverValue(container);

    const receiverDiv = document.createElement("div");
    receiverDiv.setAttribute("id", `receiver-field-${index}`);
    receiverDiv.className = "relative border border-gray-200 rounded-lg p-4 mb-4 bg-gray-50";

    receiverDiv.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-sm text-gray-600 mb-1">Receiver Name:</label>
                <input type="text" name="receivers-${index}-name" required"
                        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label class="block text-sm text-gray-600 mb-1">Email:</label>
                <input type="email" name="receivers-${index}-email_id" required"
                        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500">
            </div>
        </div>
        <button type="button"
                class="absolute top-2 right-2 text-red-600 text-xs font-medium hover:underline"
                onclick="removeReceiver('receiver-field-${index}')">
            Remove
        </button>
    `;

    container.appendChild(receiverDiv);
}


// Remove receiver input field
function removeReceiver(id) {
    var container = document.getElementById("receiver-fields");
    var field = document.getElementById(id);
    if (field) {
        field.remove();
    }
    container.removeChild(id);
}

// Show note details in a popup
function showNoteDetails(note) {
    document.getElementById('note-overlay').style.display = 'flex';

    document.getElementById('note-name').innerText = `Note Title: ${note.title}`;
    document.getElementById('note-title').innerText = `Content: ${note.content}`;
    var receiverList = document.getElementById('receiver-list');
    receiverList.innerHTML = '';
    note.receivers.forEach(function(receiver) {
        var li = document.createElement('li');
        li.innerText = `${receiver.name} - ${receiver.email_id}`;
        receiverList.appendChild(li);
    });
    document.getElementById('notes-details-popup').style.display = 'block';

}


// Close the note details popup
function closeNotesPopup() {
    document.getElementById('note-overlay').style.display = 'none';
    document.getElementById('notes-details-popup').style.display = 'none';
    document.getElementById('del-note-consent').style.display = 'none';
}

function findFirstMissingReceiverValue(divObj){
    var len = divObj.children.length;
    let indexes = [];
    for(let div in divObj.children) {
        indexes.push(divObj.children[div].id);
    }
    for (let i=0;i < len; i++){
        if(!indexes.includes('receiver-field-'+i))
            return i;
    }
    return len;
}

function showNotesDeleteAlert(note, deleteUrl) {
    document.getElementById('note-overlay').style.display = 'flex';

    document.getElementById('del-note-name').innerText = `Title: ${note.title}`;

    var delNoteConsent = document.getElementById('del-note-consent');
    delNoteConsent.style.display = 'block';

    var delBtn = delNoteConsent.querySelector('.del-note-btn');

    // ✅ Remove old click handlers
    var newDelBtn = delBtn.cloneNode(true);
    delBtn.parentNode.replaceChild(newDelBtn, delBtn);

    // ✅ Add a new one
    newDelBtn.addEventListener('click', () => {
        window.location.href = deleteUrl;
    });
}
