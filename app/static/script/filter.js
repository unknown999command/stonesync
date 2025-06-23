document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('orders-container');
    const style = document.createElement('style');
    style.innerHTML = `
        .order {
            opacity: 1;
            max-height: 1000px;
            overflow: hidden;
            transition: opacity 0.2s ease, max-height 0.2s ease;
        }

        .order.hidden {
            opacity: 0;
            max-height: 0;
            transition: opacity 0.2s ease, max-height 0.2s ease;
        }

        .order.sorted {
            opacity: 0.5;
        }
        `;
    document.head.appendChild(style);

    function filterOrders() {
        const address = document.getElementById('filter-address').value.toLowerCase();
        const customerName = document.getElementById('filter-customer').value.toLowerCase();
        const status = document.getElementById('filter-status').value;
        const selectedDate = document.getElementById('filter-date').value;
        const formattedSelectedDate = selectedDate ? selectedDate.split('T')[0] : '';
        const orders = Array.from(container.getElementsByClassName('order'));

        orders.forEach(order => {
            const orderAddress = (order.getAttribute('data-address') || '').toLowerCase();
            const orderCustomerName = (order.getAttribute('data-customer') || '').toLowerCase();
            const orderStatus = order.getAttribute('data-status') || '';
            const orderDate = (order.getAttribute('data-date') || '').split(' ')[0];
            const orderDeadline = (order.getAttribute('data-deadline') || '').split(' ')[0];

            const matchesAddress = address === '' || orderAddress.includes(address);
            const matchesCustomer = customerName === '' || orderCustomerName.includes(customerName);
            const matchesStatus = status === '' || orderStatus === status;
            const matchesDate = formattedSelectedDate === '' || [orderDate, orderDeadline].includes(formattedSelectedDate);

            if (matchesAddress && matchesCustomer && matchesStatus && matchesDate) {
                order.classList.remove('hidden');
                order.style.display = '';
            } else {
                order.classList.add('hidden');
                order.style.display = 'none';
            }
        });
    }
    document.getElementById('filter-address').addEventListener('input', filterOrders);
    document.getElementById('filter-customer').addEventListener('input', filterOrders);
    document.getElementById('filter-status').addEventListener('change', filterOrders);
    document.getElementById('filter-date').addEventListener('change', filterOrders);
});