from django.urls import path

from . import views

urlpatterns = [
    path("inbox/", views.inbox_view, name="inbox"),
    path("inbox/unread/", views.unread_count_view, name="unread_count"),
    path("conversations/<int:pk>/", views.conversation_view, name="conversation"),
    path("conversations/<int:pk>/messages/", views.messages_since_view, name="messages_since"),
    path("conversations/<int:pk>/send/", views.send_message_view, name="send_message"),
    path("listings/<int:listing_pk>/message/", views.start_conversation_view, name="start_conversation"),
]