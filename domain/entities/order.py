


class Order:
    def __init__(self, id, user_id, payment_id, order_date, address, total, status):
        self.id = id
        self.user_id = user_id
        self.payment_id = payment_id
        self.order_date = order_date
        self.address = address
        self.total = total
        self.status = status
