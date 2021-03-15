import json
import uuid
from datetime           import datetime, timedelta
from json               import JSONDecodeError

from django.db          import transaction
from django.db.models   import Q
from django.http        import JsonResponse
from django.views       import View
from django.utils       import timezone

from order.models       import Cart,Order,OrderStatus
from product.models     import MatchingReview, Product
from user.models        import Address, User
from utils              import login_decorator


SHOPPING_BASKET = '장바구니'

class CartView(View):
    @login_decorator
    def post(self, request, *args, **kwargs):
        try:
            data         = json.loads(request.body)
            user         = request.user
            product_id   = data['productId']
            total_price  = data['totalPrice']
            quantity     = data['quantity']
            order_status = OrderStatus.objects.get(name=SHOPPING_BASKET) # model에서 default값으로 박는다면?

            if not Order.objects.filter(user=user, status=order_status).exists():
                order = Order.objects.create(
                    user    = user
                    status  = order_status,
                    serial_number = str(uuid.uuid4()), # 매번 unique한 값을 만들어주는 
                )
                Cart.objects.create(
                    order       = order,
                    product_id  = product_id,
                    quantity    = quantity,
                    total_price = int(total_price),
                )
                return JsonResponse({'message': 'SUCCESS'}, status=200)

            order = Order.objects.get(user=user, status=order_status)
            if not Cart.objects.get(user=user, status=order_status).exists():
                Cart.objects.create(
                    order       = order,
                    product_id  = product_id,
                    quantity    = quantity,
                    total_price = int(total_price),
                )
                return JsonResponse({'message':'SUCCESS'}, status=200)
        except JSONDecodeError as err               : error = err       
        except KeyError as err                      : error = err
        except Product.DoesNotExist as err          : error = err
        except Order.DoesNotExist as err            : error = err
        except Order.MultipleObjectsReturned as err : error = err
        finally : 
            return JsonResponse({'message':error}, status=400)

    @login_decorator
    def get(self, request, *args, **kwargs):
        try:
            user       = request.user
            order      = Order.objects.get(user=user, status__name=SHOPPING_BASKET)
            carts = order.cart_set.all()
            result = [{
                    'cartId'    : cart.id,
                    'productId' : cart.product_id,
                    'product'   : cart.product.name,
                    'option'    : cart.option,
                    'quantity'  : cart.quantity,
                    'totalPrice': int(cart.total_price),
                    'eachPrice' : cart.product.price,
                    'urlImage'  : cart.product.image_url,
                }for cart in carts] 
            return JsonResponse({'message':'SUCCESS', 'result':result}, status=200)
        except Order.DoesNotExist as err:
            return JsonResponse({'message': err}, status=400)
    
    @login_decorator
    def delete(self, request, *args, **kwargs):
        try:
            cart_id_list = request.GET.getlist('cartId', None) # reference http://yong27.biohackers.net/303
            int_cart_id  = [int(cart_id) for cart_id in cart_id_list]
            cart         = Cart.objects.filter(id__in=int_cart_id)

            if not cart.exists():
                return JsonResponse({'message': 'DOES_NOT_EXIST'}, status=400)
            
            cart.delete()
            return JsonResponse({'message':'SUCCESS'}, status=200)
        except JSONDecodeError as err:          error = err
        except KeyError as err:                 error = err
        except Order.DoesNotExist as err:       error = err
        except OrderStatus.DoesNotExist as err: error = err
        finally : 
            return JsonResponse({'message':error}, status=400)


class PaymentView(View):
    @login_decorator:
    def get(self, request, *args, **kwargs):
        try:
            user    = request.user
            order   = Order.objects.get(user=user, status__name=SHOPPING_BASKET)

            product_info =[{
                "cartId"        : cart_list.id,
                "productId"     : cart_list.product_id,
                "product"       : cart_list.product.name,
                "option"        : cart_list.option,
                "quantity"      : cart_list.quantity,
                "totalPrice"    : cart_list.total_price,
                "eachPrice"     : cart_list.product.price,
                "urlImage"      : cart_list.product.image_url,
            } for cart_list in order.cart_set.all() ]
            
            user_info = {
                'userName'          : user.name,
                'userHomeAddress'   : user.home_address,
                'userHomePhone'     : user.home_phone,
                'userCellPhone'     : user.cell_phone,
                'userEmail'         : user.email,
            }
            
            user_address_info = {
                'toPerson'          : user.name,
                'userHomeAddress'   : user.home_address,
                'userHomePhone'     : user.home_phone,
                'userCellPhone'     : user.cell_phone,
            }

            return JsonResponse({
                'message':'SUCCESS',
                'results':{
                    'product_info'     : product_info,
                    'user_info'        : user_info,
                    'user_address_info': user_address_info,
                }
            }, status=200)
        except Address.DoesNotExist          as err : error=err
        except Order.DoesNotExist            as err : error=err
        except Order.MultipleObjectsReturned as err : error=err
        except OrderStatus.DoesNotExist      as err : error=err
        finally:
            return JsonResponse({'message':error}, status=400)

def get_order_list(request):
    compare_date = timezone.localtime() - timedelta(days=7)
    user         = request.user
    start_date   = request.GET.get('startDate', compare_date)
    end_date     = request.GET.get('endDate', timezone.localtime())

    orders = Order.objects.filter(\
                user_id=user.id,\
                create_at__range=(start_date, end_date))

    result = [{
        'serialNumber' : order.serial_number,
        'orderStatus'  : order.status.id,
        'orderDate'    : order.create_at,
        'orderId'      : order.id,
        'subProducts'  : [{
            'id'            : cart.product.id,
            'name'          : cart.product.name,
            'totalPrice'    : cart.total_price,
            'quantity'      : cart.quantity,
            'productStatus' : cart.status.id,
            'isReview'      : MatchingReview.objects.filter(order=order.id, product=cart.product).exists()
        }for cart in order.cart_set.all()]
    }for order in orders]

    return result

class OrderListView(View):
    @login_decorator
    def get(self, request):
        result = get_order_list(request)
        return JsonResponse({'message':'SUCCESS', 'data':result}, status=200)

    @login_decorator
    def patch(self, request):
        CONFIRM_STATUS = 4

        data = json.loads(request.body)

        try:
            order_id   = data['orderId']
            product_id = data['productId']
            
            product = Cart.objects.get(order_id=order_id, product_id=product_id)
            product.status_id = CONFIRM_STATUS
            product.save()

            result = get_order_list(request)

            return JsonResponse({'message':'SUCCESS', 'data': result}, status=200)
        except KeyError          as e: error=e
        except Cart.DoesNotExist as e: error=e
        finally:
            return JsonResponse({'message':error}, status=400) 