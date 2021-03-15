import json
from datetime           import datetime, timedelta

from django.utils       import timezone
from django.views       import View
from django.http        import JsonResponse
from django.db.models   import Q
from django.db          import transaction, IntegrityError

from utils              import login_decorator
from user.models        import User
from order.models       import Order, Cart
from order.views        import get_order_list
from product.models     import (
    ProductDetailView, 
    ProductListView, 
    ReviewView, 
    ProductLikeView
    )

def is_new(create_at, compare_date):
    return create_at > compare_date

def check_best_list():
    best_query = Product.objects.all().order_by('total_sales')[:20]
    return [best.id for best in best_query]

def is_best(checkList, id):
    return id in checkList

def is_sale(sale):
    return sale > 0


class ProductListView(View):
    def get(self, request):
        category_name = request.GET.get('category', 'None')
        sorting       = request.GET.get('sorting', '-total_sales')
        best_list     = check_best_list()
        compare_date  = timezone.localtime() - timedelta(days=30) # 과거 30이전 

        product_list  = Product.objects.all().order_by(sorting(sorting) \
            if category_name is None or category_name == '전체' \
            else Product.objects.filter(category__name=category_name).order_by(sorting)

        products = [{
                     'id'        : item.id,
                     'name'      : item.name,
                     'price'     : item.price,   
                     'sale'      : item.sale,   
                     'stock'     : item.stock,   
                     'imageUrl'  : item.image_url,       
                     'category'  : item.category.id, 
                     'isNew'     : is_new(item.create_at, compare_date),  
                     'isBest'    : is_best(best_list, item.id),   
                     'isSale'    : is_sale(item.sale),   
                } for item in product_list]
        return JsonResponse({'data' : {'products': products }}, status=200 )


class ProductDetailView(View):
    def get(self, request, product_id):
        if not Product.objects.filter(id = product_id).exists():
            return JsonResponse({'message': 'PRODUCT_DOES_NOT_EXISTS'}, status=404)

        product = Product.objects.get(id=product_id)
        reviews = product.review_set.all()
        images  = product.productimage_set.all()

        product_view = {
            'id'          : product.id, 
            'name'        : product.name,
            'price'       : product.price,
            'sale'        : product.sale,
            'stock'       : product.stock,
            'thumbnailUrl': product.image_url,
            'imageUrls'   : [image.image_url for image in images],
            'reviews':[{
                        'id'          : review.id,
                        'reviewTitle' : review.title,
                        'content'     : review.content, 
                        'starRating'  : review.star_raing, 
                        'createAt'    : review.create_at, 
                        'userId'      : review.user.account, 
                                            }for review in reviews]
        }
        return JsonResponse({'data':{'product': product_view}}, status=200)


class ProductLikeView(View):
    @login_decorator
    def get(self, request):

        likes = request.user.productlike_set.all()
        likes = [{
            'id'       : like.product.id,
            'name'     : like.product.name,
            'imageUrl' : like.product.image_url,
            'category' : like.product.category.id,
        }for like in likes]

        return JsonResponse({'message':'SUCCESS', 'data':likes}, status=200)
    
    @login_decorator
    def post(self, request):
        data = json.loads(request.body)

        have_like, is_have_like = ProductLike.objects.get_or_create(\
                                 user_id=request.user.id, 
                                 product_id=data['productId'])
        
        if not is_have_like: have_like.delete() # 좋아요 이전에 했기에 다시 좋아요를 한것은 언팔로우 하려는 의도와 동일한 로직

        return JsonResponse({'message':'SUCCESS'}, status=200)

class MainView(View):
    def get(self, request):
        compare_date = timezone.localtime() - \
            timedelta(days=30)+timedelta(days=-30)
        checkBest = check_best_list()

        BEST_COUNT = 4
        NEW_COUNT = 8
        SALE_COUNT = 8

        best_query = Product.objects.all().order_by('-total_sales')[:BEST_COUNT]
        best_list = [{
            'id'        : best.id,
            'name'      : best.name,
            'imageUrl'  : best.image_url,
            'category'  : best.category.id,
            'price'     : best.price,
            'sale'      : best.sale,
            'isNew'     : is_new(best.create_at, compare_date),
            'isBest'    : is_best(checkBest, best.id),
            'isSale'    : is_sale(best.sale),
        }for best in best_query]

        new_query = Product.objects.all().order_by('-sale')[:NEW_COUNT]
        new_list = [{
            'id'        : new.id,
            'name'      : new.name,
            'imageUrl'  : new.image_url,
            'category'  : new.category.id,
            'price'     : new.price,
            'sale'      : new.sale,
            'isNew'     : is_new(new.create_at, compare_date),
            'isBest'    : is_best(checkBest, new.id),
            'isSale'    : is_sale(new.sale),
        }for new in new_query]

        sale_query = Product.objects.filter(sale__gt=0)[:SALE_COUNT]
        sale_list = [{
            'id'        : sale.id,
            'name'      : sale.name,
            'imageUrl'  : sale.image_url,
            'category'  : sale.category.id,
            'price'     : sale.price,
            'sale'      : sale.sale,
            'isNew'     : is_new(sale.create_at, compare_date),
            'isBest'    : is_best(checkBest, sale.id),
            'isSale'    : is_sale(sale.sale),
        }for sale in sale_query]
        return JsonResponse({
            'message' : 'SUCCESS',
            'data'    : {
                'best' : best_list,
                'new'  : new_list,
                'sale' : sale_list 
            }}, status=200)


class ReviewView(View):
    def get(self, request, product_id):
        reviews = Review.objects.filter(product_id=product_id)
        reviews = [{
            'user'      : review.user.account,
            'content'   : review.content,
            'starRating': review.start_rating,
            'imageUrl'  : review.image_url,
            'createAt'  : review.create_at,
        }for review in reviews]
        return JsonResponse({'message':'SUCCUSS', 'data': reviews}, status=200)
    
    @login_decorator
    def post(self,request):
        data = json.loads(request.body)
        user - request.user

        try:
            product_id = data['productId']
            order_id   = data['orderId']

            check_matching = MatchingReview.objects.filter(product_id=product_id,\
                                                           order_id=order_id)
            if check_matching.exists():
                return JsonResponse({'message':'ALREADY_HAVE_ITEM'}, status=400)
            
            with transaction.atomic():
                review = Review.objects.create(
                    product_id  = product_id,
                    user_id     = request.user.id,
                    title       = data['title']
                    content     = data['content']
                    star_rating = data['starRating']
                    image_url   = data['imageUrl'] if data.get(image_url') else 'none'
                )

                MatchingReview.objects.create(
                    review = review,
                    order_id = order_id,
                    product_id = product_id,
                )
            result = get_order_list(request)
        return JsonResponse({'message':'SUCCESS', 'data': result}, status=200)
        
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
        except IntegrityError:
            return JsonResponse({'message':'INTEGRITY_ERROR'}, status=400)