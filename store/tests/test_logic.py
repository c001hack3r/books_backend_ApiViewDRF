from django.test import TestCase
from store.logic import set_rating
from django.contrib.auth.models import User
from store.models import Book, UserBookRelation


class SetRatingTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username = 'user1', first_name="Ivan", last_name='Petrov')
        self.user2 = User.objects.create(username = 'user2', first_name="Ivan", last_name='Sidorov')
        self.user3 = User.objects.create(username = 'user3', first_name="1", last_name='2')
        
        self.book1 = Book.objects.create(name='Test book 1', price = 25, author_name = 'Author 1', owner = self.user1)
         
        UserBookRelation.objects.create(user=self.user1, book = self.book1, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user2, book = self.book1, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user3, book = self.book1, like=True, rate=4)
            
    
    def test_ok(self): 
        set_rating(self.book1)
        self.book1.refresh_from_db()
        self.assertEqual('4.67', str(self.book1.rating))