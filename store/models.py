from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    author_name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                            null=True, related_name='my_books')
    readers = models.ManyToManyField(User, through = 'UserBookRelation',
                                     related_name='books')
    discount = models.DecimalField(max_digits=5,decimal_places=2, default='15.00')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=None, null=True)
    
    def __str__(self):
        return f'ID: {self.id}: {self.name}, price: {self.price}'
    
    
class UserBookRelation(models.Model):
    RATE_CHOICES = [
        (1, 'Ok'),
        (2, 'Fine'),
        (3, 'Good'),
        (4, 'Amazing'),
        (5, 'Incredible'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    in_bookmarks = models.BooleanField(default=False)
    rate = models.PositiveSmallIntegerField(choices=RATE_CHOICES, null=True)
    
    def __str__(self):
        return f'{self.user.username}: {self.book.name}, rate: {self.rate}'
    
    
    def __init__(self, *args, **kwargs):
        super(UserBookRelation, self).__init__(*args, **kwargs)
        self.old_rate = self.rate

    def save(self, *args, **kwargs):
        creating = not self.pk

        super().save(*args, **kwargs)

        if self.old_rate != self.rate or creating:
            from store.logic import set_rating
            set_rating(self.book)
        