function createElement(tag, attrs = {}, text = '') {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    if (text) el.textContent = text;
    return el;
}

function loadCalls() {
    const client = document.getElementById('clientCode').value.trim();
    if (!client) return;
    fetch(`/api/calls/${client}`)
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('calls');
            list.innerHTML = '';
            data.forEach(call => {
                const item = createElement('li', { class: 'list-group-item', 'data-id': call.id });
                item.textContent = `${call.id} - ${call.title}`;
                item.addEventListener('click', () => loadTicket(call.id));
                list.appendChild(item);
            });
        });
    fetch(`/api/forms/${client}`)
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('forms');
            list.innerHTML = '';
            data.forEach(form => {
                const item = createElement('li', { class: 'list-group-item' }, `${form.id} - ${form.subject}`);
                list.appendChild(item);
            });
        });
}

document.getElementById('loadCalls').addEventListener('click', loadCalls);

document.getElementById('createForm').addEventListener('click', () => {
    const client = document.getElementById('formClient').value.trim();
    const subject = document.getElementById('formSubject').value.trim();
    const description = document.getElementById('formDescription').value.trim();
    fetch('/api/forms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client, subject, description })
    })
        .then(r => r.json())
        .then(() => loadCalls());
});

function loadTicket(id) {
    fetch(`/api/call/${id}`)
        .then(r => r.json())
        .then(data => {
            const div = document.getElementById('ticketDetails');
            div.innerHTML = '';
            Object.entries(data).forEach(([k, v]) => {
                const p = createElement('p');
                p.innerHTML = `<strong>${k}:</strong> ${v}`;
                div.appendChild(p);
            });
        });
}
