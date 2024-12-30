function scanBarcode() {
    fetch('/scan', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
    });
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
                d.innerText = data.total_amount.toLocaleString("en");


            let t = document.getElementById(`book${id}`);
            t.style.display = "none";
        });
    }
}

function pay() {
    if (confirm("Bạn chắc chắn thanh toán!") === true) {
        const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
        fetch("/api/pay", {
            method: "post",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ payment_method: paymentMethod })
        }).then(res => res.json()).then(data => {
            if (data.status === 200)
            {
                if (data.method === "cash"){
                    const message= document.getElementById("message");
                    message.innerHTML = `<div class="alert alert-success" role="alert">${data.msg}</div>`;
                    location.reload();
                }
                if (data.method==="card"){
                    const message = document.getElementById("message");
                    message.innerHTML = `<div class="alert alert-success" role="alert">${data.msg}</div>`;
                }
            }
            else
                alert(data.err_msg)
        })
    }
}
