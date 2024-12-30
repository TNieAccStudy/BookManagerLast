
function showToast(idElement,classToastContainer) {
    var toastContainer = document.querySelector(classToastContainer);
    toastContainer.style.display = 'block';

    var toastEl = document.getElementById(idElement);
    var toast = new bootstrap.Toast(toastEl, { delay: 1000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', function () {
        toastContainer.style.display = 'none';
    });
}
function addToCart(id, title, price,image) {
    fetch("/api/cart", {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "title": title,
            "price": price,
            "image": image
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(function(res) {
        return res.json();
    }).then(function(data) {
        let carts = document.getElementsByClassName("cart-counter");
        for (let d of carts)
            d.innerText = data.total_quantity;
        showToast('liveToast','.toast-container');
        const data_book =data.books;
        const c= data_book[id];
        let book = document.getElementById(`book${id}`);
        console.log(book);
        if (book) {
            book.remove();
        }
        let noProductElement = document.querySelector('.header__cart-list-item.d-flex');
        if (noProductElement) {
            noProductElement.remove();
        }
        let cartList =document.getElementById("cart-list") ;
        if (!cartList) {
            cartList = document.createElement("ul");
            cartList.className = "header__cart-list-item";
            cartList.id = "cart-list";
            document.querySelector('.header__cart-list').appendChild(cartList);
        }
        let html =`<li class="header__cart-item book${c.id} border-bottom"style="margin:20px 0 0 20px" id="book${c.id}">
        <img src="${c.image}" alt="" class="header__cart-img"> 
        <div class="header__cart-item-info">
            <div class="header__cart-item-head">
                <h5 class="header__cart-item-name">${c.title}</h5>
                <div class="header__cart-item-price-wrap">
                <span class="header__cart-item-price">${c.price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).replace(/,/g, '.')}</span>
                    <span class="header__cart-item-multiply">x</span>
                    <span class="header__cart-item-quantity cart_quantity${c.id}">${c.quantity}</span>
                </div>
            </div>
        </div>
    </li>`;
        let cardList =document.getElementById("cart-list") ;
        cardList.innerHTML = html +cardList.innerHTML;
        let viewCartButton = document.querySelector('.header__cart-view-cart');
        if (!viewCartButton) {
            viewCartButton = document.createElement("a");
            viewCartButton.href = "/cart";
            viewCartButton.className = "header__cart-view-cart button btn--primary";
            viewCartButton.innerText = "Xem giỏ hàng";
            document.querySelector('.header__cart-list').appendChild(viewCartButton);
        }
    });
}

function updateCart(id, obj) {
    obj.disabled = true;
    fetch(`/api/cart/${id}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value,
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(function(res) {
        return res.json();
    }).then(function(data) {
        console.log(data);
        obj.disabled = false;
        let carts = document.getElementsByClassName("cart-counter");
        let quantitys = document.getElementsByClassName(`cart_quantity${id}`);
        let price_final = document.getElementsByClassName(`price_final${id}`);
        for (let d of carts)
            d.innerText = data.total_quantity;
        for (let d of quantitys)
            d.innerText = data.books[id].quantity;
        for (let d of price_final)
            d.innerText = (data.books[id].price * data.books[id].quantity).toLocaleString('vi-VN', { minimumFractionDigits: 0 }).replace(/,/g, '.') + " VNĐ";
        let amounts = document.getElementsByClassName("cart-amount");
        console.log(`count amount ${amounts.length}`)
        console.log(data.total_amount);
        for (let d of amounts)
            d.innerText = data.total_amount.toLocaleString("en").replace(/,/g,'.') + "VNĐ";
    }).catch(function(error) {
        console.error('Error:', error);
        obj.disabled = false;
    });
}

function updateSelection(id, checkbox) {
    const isSelected = checkbox.checked;
    checkbox.disabled = true;
    fetch(`/api/cart/${id}/select`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_selected: isSelected })
    }).then(response => response.json())
      .then(data => {
          checkbox.disabled = false;
        console.log('Selection updated successfully');
        let amounts = document.getElementsByClassName("cart-amount");
        console.log(`count amount ${amounts.length}`)
        for (let d of amounts)
            d.innerText = data.total_amount.toLocaleString("en").replace(',','.') +'VNĐ';
      }).catch(error => {
          console.error('Error:', error);
          checkbox.disabled = false;
          checkbox.checked = !isSelected;
      });
}

function updateAllSelections(ids, isSelected) {
    fetch(`/api/cart/select-all`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: ids,is_selected: isSelected })
    }).then(response => response.json())
      .then(data => {
        console.log('Selection updated successfully');
        let amounts = document.getElementsByClassName("cart-amount");
        for (let d of amounts)
            d.innerText = data.total_amount.toLocaleString("en").replace(',','.') +'VNĐ';
      }).catch(error => {
          console.error('Error:', error);
          ids.forEach(id => {
            const checkbox = document.querySelector(`#books${id} .item-checkbox`);
            checkbox.checked = !isSelected;
        });
      });
}

function submitCheckout() {
    const selectedItems = [];
    document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
        selectedItems.push(checkbox.closest('tr').id.replace('books', ''));
    });
    document.getElementById('selected-items').value = JSON.stringify(selectedItems);
    document.getElementById('checkout-form').submit();
}
function deleteCart(id, obj) {
    if (confirm("Bạn chắc chắn xóa?") === true) {
        obj.disabled = true;
        fetch(`/api/cart/${id}`, {
            method: "delete"
        }).then(function(res) {
            return res.json();
        }).then(function(data) {
            obj.disabled = false;
            let carts = document.getElementsByClassName("cart-counter");
            for (let d of carts)
                d.innerText = data.total_quantity;

            let amounts = document.getElementsByClassName("cart-amount");
            for (let d of amounts)
                d.innerText = data.total_amount.toLocaleString("en").replace(',','.') +'VNĐ';


            let elements = document.getElementsByClassName(`book${id}`);
            while (elements.length > 0) {
                elements[0].parentNode.removeChild(elements[0]);
            }
            const cartItems = document.querySelectorAll('tr[class^="book"]');
            console.log(cartItems.length);
            if (cartItems.length === 0) {
                location.reload();
            }
        });
    }
}

function deleteOrder(id, obj) {
    if (confirm("Bạn chắc chắn hủy?") === true) {
        obj.disabled = true;
        fetch(`/api/order/${id}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            if (data.status === 200)
                location.reload();
            else
            alert(data.err_msg)
        })
    }
}

function requestCancelOrder(id, obj) {
    const reason = document.getElementById('reason').value;
    if (confirm("Bạn chắc chắn muốn hủy đơn hàng?") === true) {
        obj.disabled = true;
        fetch(`/orders/${id}/cancel`, {
            method: "post",
            body: JSON.stringify({
                "reason": reason
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data => {
            if (data.status === 200) {
                alert("Yêu cầu hủy đơn hàng đã được gửi!");
                window.location.href = '/historyorder';
            } else {
                alert(data.err_msg);
                obj.disabled = false;
            }
        }).catch(error => {
            console.error('Error:', error);
            obj.disabled = false;
        });
    }
}



function pay() {
    if (confirm("Bạn chắc chắn thanh toán!") === true) {
        fetch("/api/pay", {
            method: "post"
        }).then(res => res.json()).then(data => {
            if (data.status === 200)
                location.reload();
            else
                alert(data.err_msg)
        })
    }
}

function registerUser() {
    const form = document.getElementById('form-3');
    const formData = new FormData(form);
    fetch('/register', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('liveToastRegister','.toast-container-register');
            window.location.href = '/?registered=true';
        } else {
            document.getElementById('error-message').textContent = data.err_msg;
        }
    })
    .catch(error => console.error('Error:', error));
}

function loginUser() {
    const form = document.getElementById('form-5');
    const formData = new FormData(form);
    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.err_msg) {
            document.getElementById('error-message-login').textContent = data.err_msg;
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            const nextUrl = urlParams.get('next');
            if (nextUrl) {
                window.location.href = nextUrl;
            } else {
                window.location.href = '/';
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

function addReview(book_id) {
    if (confirm("Bạn chắc chắn thêm bình luận?") === true) {
        const selectedStar = document.querySelector('.star.selected');
        const rating = selectedStar ? selectedStar.getAttribute('data-value') : 5;
        const comment = document.getElementById('comment').value;
        // alert(comment);
        fetch(`/books/${book_id}/reviews`, {
            method: "post",
            body: JSON.stringify({
                "content": comment,
                "rating": rating
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data => {
            if (data.status === 200) {
                let c = data.review;
                document.getElementById('rating').style.display = 'none';
                document.getElementById('comment').style.display = 'none';
                document.querySelector('button[onclick^="addReview"]').style.display = 'none';
                let d = document.getElementById("reviews");
                d.innerHTML = `
                <div class="row alert alert-info mb-3">
                    <div class="col-md-2 col-xs-4 fs-2">
                        <h2>${c.user.name}</h2>
                        <p><span class="date">${moment(c.created_date).locale("vi").fromNow()}</span></p>
                    </div>
                    <div class="col-md-10 col-xs-8">
                        <div class="rating fs-3 mb-2">
                            ${[...Array(c.rating)].map(() => '<span class="star text-warning">&#9733;</span>').join(' ')}
                            ${[...Array(5 - c.rating)].map(() => '<span class="star text-muted">&#9734;</span>').join(' ')}
                        </div>
                        <p class="fs-3"><strong>${c.content}</strong></p>
                    </div>
                </div>
                ` + d.innerHTML;
            } else {
                alert(data.err_msg);
            }
        });
    }
}

function checkCartAndProceed() {
    fetch('/api/check-cart')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'empty') {
                alert('Vui lòng chọn sách để đặt hàng!');
            } else {
                window.location.href = '/checkout';
            }
        })
        .catch(error => console.error('Error:', error));
}