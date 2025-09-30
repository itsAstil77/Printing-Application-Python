function toggleSelectAll(selectAllCheckbox) {
    document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

function toggleRowSelection(row) {
    const checkbox = row.querySelector('.employee-checkbox');
    checkbox.checked = !checkbox.checked;
}

function filterEmployees() {
    let input = document.getElementById("search-box").value.toLowerCase();
    let rows = document.querySelectorAll("tbody tr");  // Selecting all table rows

    rows.forEach(row => {
        let text = Array.from(row.children)  // Convert row's children (td elements) into an array
                       .map(cell => cell.textContent.toLowerCase())  // Get text from each cell
                       .join(" ");  // Join all cell texts into a single string

        if (text.includes(input)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}
function generateSelectedIdCards() {
    const checkboxes = document.querySelectorAll('.employee-checkbox:checked');
    const selectedEmployeeIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    const selectedIdCardType = document.getElementById('id-card-type-selector').value;

    if (selectedEmployeeIds.length === 0) {
        alert('Please select at least one employee.');
        return;
    }

    document.getElementById("loading-popup").style.display = "flex";

    fetch('/generate-selected-id-cards/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
            employee_ids: selectedEmployeeIds,
            card_type: selectedIdCardType
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loading-popup").style.display = "none";

        if (data.files && data.files.length > 0) {
            let previewWindow = window.open('', '', 'height=800,width=800');
            previewWindow.document.write(`
                <html>
                <head>
                    <title>Print ID Cards</title>
                    <style>
                        @page {
                            size: A4 portrait;
                            margin: 0;
                        }
                        body {
                            margin: 0;
                            padding: 0;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                        }
                        .id-card-container {
                            width: 100vw;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            page-break-before: always;
                        }
                        .id-card {
                            width: 9.5cm;
                            height: 5.7cm;
                            box-shadow: 0px 0px 5px rgba(0,0,0,0.3);
                            border-radius: 10px;
                            background-color: white;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            padding: 5px;
                        }
                        .id-card img {
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                            border-radius: 8px;
                        }
                        @media print {
                            body { display: block; }
                            .id-card-container {
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                width: 100vw;
                                height: 100vh;
                                page-break-before: always;
                            }
                            button { display: none; }
                        }
                    </style>
                </head>
                <body>
            `);

            data.files.forEach(file => {
                previewWindow.document.write(`
                    <div class="id-card-container">
                        <div class="id-card">
                            <img src="/static/app1/generated_id_cards/${file.split('/').pop()}">
                        </div>
                    </div>
                `);
            });

            previewWindow.document.write(`
                    <button onclick="window.print()">Print ID Cards</button>
                </body>
                </html>
            `);
            previewWindow.document.close();

            // ✅ Auto-refresh checkboxes after generation
            document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        } else {
            alert('No ID cards generated.');
        }
    })
    .catch(error => {
        console.error('Error generating ID cards:', error);
        document.getElementById("loading-popup").style.display = "none";
    });
}
function logout() {
    // Create a confirmation popup
    let confirmLogout = confirm("Are you sure you want to logout?");
    
    if (confirmLogout) {
        // Redirect to the login page
        window.location.href = "/login/";
    }
}





