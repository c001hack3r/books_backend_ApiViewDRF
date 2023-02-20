from rest_framework.test import APITestCase
from django.urls import reverse
from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer
from rest_framework import status
import json
from django.contrib.auth.models import User
from rest_framework.exceptions import ErrorDetail
from django.db.models import Count, Case, When, Avg, F
from django.test.utils import CaptureQueriesContext
from django.db import connection


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user= User.objects.create(username='test_username')
        self.book1 = Book.objects.create(name='Test book 1', price = 25, author_name = 'Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book 2', price = 55, author_name = 'Author 5')
        self.book3 = Book.objects.create(name='Test book Author 1', price = 55, author_name = 'Author 2')
        
        UserBookRelation.objects.create(user=self.user, book = self.book1, like=True, rate=5)
    
    def test_get(self):
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            self.assertEqual(2, len(queries))
        books = Book.objects.all().annotate(annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    discount15 = F('price') - F('discount'),
                                    owner_name = F('owner__username'),
                                    ).prefetch_related('readers').order_by('id')
        serializer_data = BooksSerializer(books, many = True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)
        
    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data = {'price': 55})
        books = Book.objects.filter(id__in = [self.book2.id, self.book3.id]).annotate(
                                    annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    discount15 = F('price') - F('discount'),
                                    owner_name = F('owner__username'),
                                    ).prefetch_related('readers').order_by('id')
        serializer_data = BooksSerializer(books, many = True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        
    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data = {'search': 'Author 1'})
        books = Book.objects.filter(id__in = [self.book1.id, self.book3.id]).annotate(
                                    annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    discount15 = F('price') - F('discount'),
                                    owner_name = F('owner__username'),
                                    ).prefetch_related('readers').order_by('id')
        serializer_data = BooksSerializer(books, many = True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        
    def test_get_search_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data = {'search': 'Author 1', 'ordering':'-price'})
        books = Book.objects.filter(id__in = [self.book1.id, self.book3.id]).annotate(
                                    annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    discount15 = F('price') - F('discount'),
                                    owner_name = F('owner__username'),
                                    ).prefetch_related('readers').order_by('-price')
        serializer_data = BooksSerializer(books, many = True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data, response.data)
        
    def test_create(self):
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-list')
        data = {
            "name": "Programming in Python 3",
            "price":  150,
            "author_name": "Mark Summerfield"
            }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(Book.objects.all().count(), 4)
        self.assertEqual(Book.objects.last().owner, self.user)

    def test_update(self):
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price":  75,
            "author_name": self.book1.author_name,
            }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(75, self.book1.price)
        
    def test_delete(self):
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-detail', args=(self.book1.id,))
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(Book.objects.all().count(), 2)
        
    def test_update_not_owner(self):
        self.user2= User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price":  75,
            "author_name": self.book1.author_name,
            }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.', code='permission_denied')},response.data)
        self.book1.refresh_from_db()
        self.assertEqual(25, self.book1.price)
    
    #forbidden /book/1/    
    def test_update_not_owner_but_staff(self):
        self.user2= User.objects.create(username='test_username2', is_staff = True)
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price":  75,
            "author_name": self.book1.author_name,
            }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(75, self.book1.price)
    
    #forbidden /book/1/   
    def test_delete_not_owner_or_staff(self):
        self.user3= User.objects.create(username='test_username3')
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-detail', args=(self.book1.id,))
        self.client.force_login(self.user3)
        response = self.client.delete(url)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.', code='permission_denied')},response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(Book.objects.all().count(), 3)
        
class BooksRelationTestCase(APITestCase):
    def setUp(self):
        self.user= User.objects.create(username='test_username')
        self.user2= User.objects.create(username='test_username2')
        self.book1 = Book.objects.create(name='Test book 1', price = 25, author_name = 'Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book 2', price = 55, author_name = 'Author 5')
    
    def test_like_and_bookmarks(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "like": True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertTrue(relation.like)
        
        data = {
            "in_bookmarks": True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertTrue(relation.in_bookmarks)
        
    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "rate": 3,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertEqual(3, relation.rate)
        
    #Bad Request: /book_relation/1/   
    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "rate": 6,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'rate': [ErrorDetail(string='"6" is not a valid choice.', code='invalid_choice')]} ,response.data)

        