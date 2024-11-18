function showEmployeeDetails(username) {
    fetch(`/get_employee/${username}`)
        .then(response => response.json())
        .then(data => {
            // הצגת פרטי העובד
        });
}

function removeFromShift(day, shiftIndex, employee) {
    if (confirm('האם אתה בטוח שברצונך להסיר את העובד מהמשמרת?')) {
        fetch('/remove_from_shift', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                day: day,
                shift_index: shiftIndex,
                employee: employee
            })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });
    }
}

function assignSelectedEmployee(day, shiftIndex) {
    const selectElement = document.getElementById(`employee-${day}-${shiftIndex}`);
    const employee = selectElement.value;
    
    if (!employee) {
        alert('נא לבחור עובד');
        return;
    }
    
    fetch('/assign_shift', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            day: day,
            shift_index: shiftIndex,
            employee: employee
        })
    }).then(response => {
        if (response.ok) {
            location.reload();
        }
    });
} 