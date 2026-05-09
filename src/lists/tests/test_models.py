"""Tests for the lists models."""

import pytest
from django.db import IntegrityError

from app.models import Item, MediaTypes, Sources
from lists.models import CustomList, CustomListItem
from users.models import User


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
    )


@pytest.fixture
def user2(db):
    """Create a second test user."""
    return User.objects.create_user(
        username='testuser2',
        password='testpass123',
    )


@pytest.fixture
def user3(db):
    """Create a third test user."""
    return User.objects.create_user(
        username='testuser3',
        password='testpass123',
    )


@pytest.fixture
def item(db):
    """Create a test item."""
    return Item.objects.create(
        media_id='123',
        source=Sources.TMDB.value,
        media_type=MediaTypes.MOVIE.value,
        title='Test Movie',
        image='https://example.com/image.jpg',
    )


@pytest.fixture
def item2(db):
    """Create a second test item."""
    return Item.objects.create(
        media_id='456',
        source=Sources.TMDB.value,
        media_type=MediaTypes.MOVIE.value,
        title='Another Movie',
        image='https://example.com/image2.jpg',
    )


class TestCustomList:
    """Tests for CustomList model."""

    def test_create_custom_list(self, user):
        """Test creating a custom list."""
        custom_list = CustomList.objects.create(
            name='My Favorites',
            description='My favorite movies',
            owner=user,
        )
        assert custom_list.name == 'My Favorites'
        assert custom_list.owner == user
        assert str(custom_list) == 'My Favorites'

    def test_list_ordering(self, user):
        """Test that lists are ordered by name."""
        CustomList.objects.create(name='Zebra', owner=user)
        CustomList.objects.create(name='Alpha', owner=user)
        CustomList.objects.create(name='Beta', owner=user)

        lists = list(CustomList.objects.all())
        assert lists[0].name == 'Alpha'
        assert lists[1].name == 'Beta'
        assert lists[2].name == 'Zebra'

    def test_add_collaborator(self, user, user2):
        """Test adding a collaborator to a list."""
        custom_list = CustomList.objects.create(
            name='Shared List',
            owner=user,
        )
        custom_list.collaborators.add(user2)

        assert user2 in custom_list.collaborators.all()

    def test_image_property_with_items(self, user, item):
        """Test image property returns first item's image."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        CustomListItem.objects.create(custom_list=custom_list, item=item)

        assert custom_list.image == item.image

    def test_image_property_empty_list(self, user):
        """Test image property returns empty string for empty list."""
        custom_list = CustomList.objects.create(name='Empty List', owner=user)
        assert custom_list.image == ''


class TestCustomListPermissions:
    """Tests for CustomList permission methods."""

    def test_owner_can_view(self, user):
        """Test that owner can view the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_view(user) is True

    def test_collaborator_can_view(self, user, user2):
        """Test that collaborator can view the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        custom_list.collaborators.add(user2)
        assert custom_list.user_can_view(user2) is True

    def test_non_member_cannot_view(self, user, user2):
        """Test that non-member cannot view the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_view(user2) is False

    def test_owner_can_edit(self, user):
        """Test that owner can edit the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_edit(user) is True

    def test_collaborator_can_edit(self, user, user2):
        """Test that collaborator can edit the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        custom_list.collaborators.add(user2)
        assert custom_list.user_can_edit(user2) is True

    def test_non_member_cannot_edit(self, user, user2):
        """Test that non-member cannot edit the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_edit(user2) is False

    def test_owner_can_delete(self, user):
        """Test that owner can delete the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_delete(user) is True

    def test_collaborator_cannot_delete(self, user, user2):
        """Test that collaborator cannot delete the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        custom_list.collaborators.add(user2)
        assert custom_list.user_can_delete(user2) is False

    def test_non_member_cannot_delete(self, user, user2):
        """Test that non-member cannot delete the list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        assert custom_list.user_can_delete(user2) is False


class TestCustomListItem:
    """Tests for CustomListItem model."""

    def test_create_list_item(self, user, item):
        """Test creating a list item."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        list_item = CustomListItem.objects.create(
            custom_list=custom_list,
            item=item,
        )
        assert list_item.item == item
        assert list_item.custom_list == custom_list
        assert str(list_item) == item.title

    def test_unique_constraint(self, user, item):
        """Test that same item cannot be added twice to a list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        CustomListItem.objects.create(custom_list=custom_list, item=item)

        with pytest.raises(IntegrityError):
            CustomListItem.objects.create(custom_list=custom_list, item=item)

    def test_same_item_different_lists(self, user, item):
        """Test that same item can be in different lists."""
        list1 = CustomList.objects.create(name='List 1', owner=user)
        list2 = CustomList.objects.create(name='List 2', owner=user)

        CustomListItem.objects.create(custom_list=list1, item=item)
        CustomListItem.objects.create(custom_list=list2, item=item)

        assert CustomListItem.objects.count() == 2


class TestCustomListManager:
    """Tests for CustomListManager."""

    def test_get_user_lists_owned(self, user):
        """Test getting lists owned by user."""
        CustomList.objects.create(name='Owned List', owner=user)

        lists = CustomList.objects.get_user_lists(user)
        assert lists.count() == 1
        assert lists[0].name == 'Owned List'

    def test_get_user_lists_collaborated(self, user, user2):
        """Test getting lists where user is collaborator."""
        custom_list = CustomList.objects.create(name='Shared List', owner=user)
        custom_list.collaborators.add(user2)

        lists = CustomList.objects.get_user_lists(user2)
        assert lists.count() == 1
        assert lists[0].name == 'Shared List'

    def test_get_user_lists_both(self, user, user2):
        """Test getting both owned and collaborated lists."""
        CustomList.objects.create(name='Owned', owner=user)
        collab_list = CustomList.objects.create(name='Collaborated', owner=user2)
        collab_list.collaborators.add(user)

        lists = CustomList.objects.get_user_lists(user)
        assert lists.count() == 2

    def test_get_user_lists_excludes_others(self, user, user2):
        """Test that other users' lists are excluded."""
        CustomList.objects.create(name='User 1 List', owner=user)
        CustomList.objects.create(name='User 2 List', owner=user2)

        lists = CustomList.objects.get_user_lists(user)
        assert lists.count() == 1
        assert lists[0].name == 'User 1 List'

    def test_get_user_lists_no_duplicates(self, user, user2):
        """Test that a list isn't returned twice if user is both owner and collaborator."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        custom_list.collaborators.add(user)

        lists = CustomList.objects.get_user_lists(user)
        assert lists.count() == 1

    def test_get_user_lists_with_item(self, user, item, item2):
        """Test getting user lists with item membership annotated."""
        list1 = CustomList.objects.create(name='Has Item', owner=user)
        list2 = CustomList.objects.create(name='No Item', owner=user)
        CustomListItem.objects.create(custom_list=list1, item=item)

        lists = CustomList.objects.get_user_lists_with_item(user, item)
        lists_dict = {l.name: l.has_item for l in lists}

        assert lists_dict['Has Item'] is True
        assert lists_dict['No Item'] is False


class TestCustomListItemManager:
    """Tests for CustomListItemManager."""

    def test_get_last_added_date(self, user, item, item2):
        """Test getting last added date for a list."""
        custom_list = CustomList.objects.create(name='List', owner=user)
        CustomListItem.objects.create(custom_list=custom_list, item=item)
        last_item = CustomListItem.objects.create(custom_list=custom_list, item=item2)

        last_date = CustomListItem.objects.get_last_added_date(custom_list)
        assert last_date == last_item.date_added

    def test_get_last_added_date_empty_list(self, user):
        """Test getting last added date for empty list returns None."""
        custom_list = CustomList.objects.create(name='Empty List', owner=user)

        last_date = CustomListItem.objects.get_last_added_date(custom_list)
        assert last_date is None
