import json
from datetime import datetime

from static import Intent


def send_transaction(command, **params):
    result = []
    if command == Intent.ADD_PRODUCT or command == Intent.ADD_BAGS:
        result.append(add_command(
            'addItem',
            itemCode=int(params['code'])
        ))
    elif command == Intent.REQUEST_WEIGHTING:
        result.append(add_command(
            'subscribe',
            frequency=1000,
            type='Weight'
        ))
        result.append(add_command(
            'addItem',
            eventId=generate_eventid(),
            itemCode=int(params['code'])
        ))
        result.append(add_command(
            'unsubscribe',
            eventId=generate_eventid(),
            type='Weight'
        ))
    elif command == Intent.REMOVE_PRODUCT or command == Intent.REMOVE_BAGS:
        if 'code' in params:
            result.append(add_command(
                'deleteAll',
                itemCode=int(params['code'])
            ))
        else:
            result.append(add_command(
                'deletePosition',
                itemNumber=int(params['position'])
            ))
    elif command == Intent.REQUEST_PAYMENT:
        if 'final' in params and params['final']:
            result.append(add_command(
                'payment',
                paymentType='Card'
            ))
        else:
            result.append(add_command(
                'subTotal'
            ))
    elif command == Intent.PASS_LOYALTY:
        result.append(add_command(
            'addLoyalty',
            type='Card',
            itemCode=int(params['code'])
        ))
    elif command == Intent.ADD_PROMO_CODE:
        result.append(add_command(
            'addLoyalty',
            type='Coupon',
            itemCode=int(params['code'])
        ))
    elif command == Intent.SPEND_BONUS:
        result.append(add_command(
            'payment',
            paymentType='Loyalty',
            amount=params['amount']
        ))
    elif command == Intent.CANCEL_PAYMENT:
        result.append(add_command(
            'returnAddITem'
        ))
    elif command == Intent.CANCEL_ORDER:
        result.append(add_command(
            'deleteTransaction'
        ))

    print('——— JSONs to TB ———')
    print('  —> ', '\n  —> '.join(map(json.dumps, result)), sep='')
    print('——————')


def add_command(command, **params):
    return {
        'action': command,
        'eventId': generate_eventid(),
        **params
    }


def generate_eventid():
    return 'sco' + str(int(datetime.now().timestamp() * 100000))
