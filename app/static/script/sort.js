const sortDirections = {
    date: true,
    status: true,
    manufacturer: true,
    deadline: true
};

function applySortAnimation(ordersArray) {
    ordersArray.forEach(order => {
        order.classList.add('sorted');
        order.style.maxHeight = `${order.scrollHeight}px`;
    });

    setTimeout(() => {
        ordersArray.forEach(order => {
            order.classList.remove('sorted');
            order.style.maxHeight = '';
        });
    }, 100);
}

function resetSortDirections(except) {
    Object.keys(sortDirections).forEach(key => {
        if (key !== except) {
            sortDirections[key] = true;
            document.getElementById(`sort-${key}`).textContent = {
                date: 'Дата создания',
                status: 'Статус',
                manufacturer: 'Изготовитель',
                deadline: 'Дата выполнения'
            }[key];
        }
    });
}

function sortAndUpdateUI(sortKey, sortFunction) {
    resetSortDirections(sortKey);
    const container = document.getElementById('orders-container');
    const ordersArray = Array.from(container.getElementsByClassName('order'));

    ordersArray.sort(sortFunction);

    sortDirections[sortKey] = !sortDirections[sortKey];
    document.getElementById(`sort-${sortKey}`).textContent = {
        date: `Дата создания ${sortDirections.date ? '▲' : '▼'}`,
        status: `Статус ${sortDirections.status ? '▲' : '▼'}`,
        manufacturer: `Изготовитель ${sortDirections.manufacturer ? '▲' : '▼'}`,
        deadline: `Дата выполнения ${sortDirections.deadline ? '▲' : '▼'}`,
    }[sortKey];

    applySortAnimation(ordersArray);

    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    ordersArray.forEach(order => container.appendChild(order));
}

document.getElementById('sort-date').addEventListener('click', () => {
    sortAndUpdateUI('date', (a, b) => {
        const dateA = new Date(a.getAttribute('data-date'));
        const dateB = new Date(b.getAttribute('data-date'));
        return sortDirections.date ? dateA - dateB : dateB - dateA;
    });
});

document.getElementById('sort-status').addEventListener('click', () => {
    sortAndUpdateUI('status', (a, b) => {
        return sortDirections.status
            ? a.getAttribute('data-status') - b.getAttribute('data-status')
            : b.getAttribute('data-status') - a.getAttribute('data-status');
    });
});

document.getElementById('sort-manufacturer').addEventListener('click', () => {
    sortAndUpdateUI('manufacturer', (a, b) => {
        const manufacturerA = a.getAttribute('data-manufacturer') || '';
        const manufacturerB = b.getAttribute('data-manufacturer') || '';
        return sortDirections.manufacturer
            ? manufacturerA.localeCompare(manufacturerB)
            : manufacturerB.localeCompare(manufacturerA);
    });
});

document.getElementById('sort-deadline').addEventListener('click', () => {
    sortAndUpdateUI('deadline', (a, b) => {
        const dateA = a.getAttribute('data-deadline');
        const dateB = b.getAttribute('data-deadline');

        if (dateA === 'None' && dateB === 'None') return 0;
        if (dateA === 'None') return 1;
        if (dateB === 'None') return -1;

        const dateObjA = new Date(dateA);
        const dateObjB = new Date(dateB);

        return sortDirections.deadline ? dateObjA - dateObjB : dateObjB - dateObjA;
    });
});