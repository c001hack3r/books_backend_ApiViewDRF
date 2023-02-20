from django.test import TestCase
from store.serializers import BooksSerializer
from store.models import Book, UserBookRelation
from django.contrib.auth.models import User
from django.db.models import Count, Case, When, F


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username = 'user1', first_name="Ivan", last_name='Petrov')
        self.user2 = User.objects.create(username = 'user2', first_name="Ivan", last_name='Sidorov')
        self.user3 = User.objects.create(username = 'user3', first_name="1", last_name='2')
        self.book1 = Book.objects.create(name='Test book 1', price = 25, author_name = 'Author 1', owner = self.user1)
        self.book2 = Book.objects.create(name='Test book 2', price = 55, author_name = 'Author 5')
         
        UserBookRelation.objects.create(user=self.user1, book = self.book1, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user2, book = self.book1, like=True, rate=5)
        self.user_book3 = UserBookRelation.objects.create(user=self.user3, book = self.book1, like=True)
        self.user_book3.rate=4
        self.user_book3.save()
        
        UserBookRelation.objects.create(user=self.user1, book = self.book2, like=True, rate=3)
        UserBookRelation.objects.create(user=self.user2, book = self.book2, like=True, rate=4)
        UserBookRelation.objects.create(user=self.user3, book = self.book2, like=False)
    
    
    def test_ok(self):
        books = Book.objects.all().annotate(annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
                                    discount15 = F('price') - F('discount'),
                                    owner_name = F('owner__username'),
                                    ).prefetch_related('readers').order_by('id')
        data = BooksSerializer(books, many = True).data
        expected_data = [
            {
                'id': self.book1.id,
                'name': 'Test book 1', 
                'price': '25.00',
                'author_name': 'Author 1',
                'annotated_likes': 3,
                'rating': '4.67',
                'discount15': '10.00',
                'owner_name': 'user1',
                'readers': [
                    {
                    'first_name': 'Ivan',
                    'last_name': 'Petrov',
                    },
                    {
                    'first_name': 'Ivan',
                    'last_name': 'Sidorov',
                    },
                    {
                    'first_name': '1',
                    'last_name': '2',
                    },
                ]
            },
            {
                'id': self.book2.id,
                'name': 'Test book 2', 
                'price': '55.00',
                'author_name': 'Author 5',
                'annotated_likes': 2,
                'rating': '3.50',
                'discount15': '40.00',
                'owner_name': None,
                'readers': [
                    {
                    'first_name': 'Ivan',
                    'last_name': 'Petrov',
                    },
                    {
                    'first_name': 'Ivan',
                    'last_name': 'Sidorov',
                    },
                    {
                    'first_name': '1',
                    'last_name': '2',
                    },
                ]
            }
        ]
        self.assertEqual(expected_data, data)