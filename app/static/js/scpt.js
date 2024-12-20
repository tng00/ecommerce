document.addEventListener('DOMContentLoaded', function () {

    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    const categoryBtn = document.getElementById('category-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');

    addToCartForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData(this);
            const url = this.action;

            fetch(url, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (response.ok) {
                    alert('Товар добавлен в корзину!');
                } else {
                    alert('Ошибка при добавлении товара в корзину');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка, попробуйте еще раз позже.');
            });
        });
    });

    categoryBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
    });

    window.addEventListener('click', function (e) {
        if (!categoryBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.style.display = 'none';
        }
    });

    const categoryLinks = document.querySelectorAll('.category-link');
    categoryLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');
            const submenu = document.getElementById(targetId);

            if (submenu) {
                submenu.style.display = submenu.style.display === 'block' ? 'none' : 'block';
            }
        });
    });
});
