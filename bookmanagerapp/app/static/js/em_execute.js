function loadListBase() {
    var data = document.getElementsByClassName('col-actions')
    // actions = [1,2,3];
    var actions = Array.from(data);
    actions.shift();
    console.log(actions);
    if (actions.length >0) {
        let dipHTML = `<a class="btn btn-primary btn-sm">X</a>`;
        for(let a of actions) 
            a.innerHTML = dipHTML;
    }
    // var test = document.getElementById("chao");
    // test.innerHTML = 'hello'
    console.log('success')
}

function confirmPendingCancel(cancel_order_id) {
    fetch(`/api/cancel_orders/${cancel_order_id}`, {
        method:"patch",
        body: JSON.stringify({
            reason_state: "CLIENTREQUIRED"
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        let item = document.getElementById(`item_${cancel_order_id}`);
        // console.log('have get');
        // console.log(`item_${cancel_order_id}`)
        item.style.display = 'none';
    })
}

function confirmOrder(order_id,context) {
    console.log(context.dataset.type)
    fetch(`/api/orders/${order_id}`, {
        method:"patch",
        body: JSON.stringify({
            'confirmedState': context.dataset.type
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        let item = document.getElementById(`item_${order_id}`);
        item.style.display='none';
    })
}

function payment() {
    var methodPayment = "";
    const cashMethod = document.getElementById("em-payment-cash");
    const cardMethod = document.getElementById("em-payment-card");
    if(cashMethod.checked) {
        methodPayment = "cash";
    }
    else if (cardMethod.checked) {
        methodPayment = "card";
    }
    fetch(`/api/em/pay`, {
        method:"post",
        body: JSON.stringify ({
            "paymentMethod": methodPayment,
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => {
        console.log(res.status);
        if (res.status == 200) return res.json();
    }).then(data => {
        window.location.href=data.redirect;
    })
}


// function testClick(context) {
//     console.log(context.dataset.type)
// }