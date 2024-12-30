def count_cart(cart):
    total_amount, total_quantiy = 0, 0
    
    if cart:
        for c in cart.values():
            total_quantiy += c['quantity']
            if 'is_selected' not in c :
                total_amount += c['quantity']*c['price']
            elif c['is_selected']:
                total_amount += c['quantity']*c['price']
            else:
                total_amount += c['quantity']*c['price']

    return {
        "total_amount": total_amount,
        "total_quantity": total_quantiy,
        "books": cart
    }


