import sys
sys.path.insert(0, 'D:\\Projet_integrateur\\PIL1_2526_61\\backend')

import pytest
from services.notification_service import creer_notification


# ─── Helpers ─────────────────────────────────────────────────

def _has(sql, *words):
    return all(w in sql for w in words)


def _user_ctx(**extras):
    base = {
        'user': {'id': 1, 'prenom': 'Test', 'nom': 'User',
                 'avatar_url': None, 'filiere_nom': 'Informatique'},
        'nb_notifs': 0,
    }
    base.update(extras)
    return base


# ─── NotificationService ─────────────────────────────────────

class TestNotificationService:

    def test_creer_notification_inserts_and_emits(self, mocker):
        mock_execute = mocker.patch('services.notification_service.execute')
        mock_fetch_one = mocker.patch('services.notification_service.fetch_one',
                                      return_value={'nb': 3})
        mock_emit = mocker.patch('app.socketio.emit')

        creer_notification(
            utilisateur_id=5,
            message="Test a besoin de votre aide !",
            type_notification="match_demande",
            correspondance_id=42
        )

        mock_execute.assert_called_once()
        sql = mock_execute.call_args[0][0]
        params = mock_execute.call_args[0][1]
        assert _has(sql, 'INSERT INTO notifications')
        assert params == (5, "Test a besoin de votre aide !", "match_demande", 42)

        mock_fetch_one.assert_called_once()
        assert _has(mock_fetch_one.call_args[0][0], 'COUNT')

        mock_emit.assert_called_once_with(
            'nouvelle_notification',
            {'nb_non_lues': 3, 'dernier_message': "Test a besoin de votre aide !",
             'type': 'match_demande', 'correspondance_id': 42},
            room='user_5'
        )

    def test_creer_notification_without_correspondance(self, mocker):
        mock_execute = mocker.patch('services.notification_service.execute')
        mocker.patch('services.notification_service.fetch_one', return_value={'nb': 1})
        mocker.patch('app.socketio.emit')

        creer_notification(
            utilisateur_id=3,
            message="Bienvenue sur MentorLink !",
            type_notification="info",
            correspondance_id=None
        )

        mock_execute.assert_called_once()
        params = mock_execute.call_args[0][1]
        assert params == (3, "Bienvenue sur MentorLink !", "info", None)

    def test_creer_notification_handles_db_error(self, mocker):
        mocker.patch('services.notification_service.execute',
                     side_effect=Exception("DB error"))
        mocker.patch('services.notification_service.fetch_one')
        mocker.patch('app.socketio.emit')

        creer_notification(
            utilisateur_id=1,
            message="Ceci va planter",
            type_notification="info"
        )

    def test_creer_notification_zero_unread(self, mocker):
        mock_execute = mocker.patch('services.notification_service.execute')
        mocker.patch('services.notification_service.fetch_one', return_value={'nb': 0})
        mock_emit = mocker.patch('app.socketio.emit')

        creer_notification(
            utilisateur_id=2,
            message="Message test",
            type_notification="info",
            correspondance_id=None
        )

        mock_execute.assert_called_once()
        mock_emit.assert_called_once()
        data = mock_emit.call_args[0][1]
        assert data['nb_non_lues'] == 0
        assert data['type'] == 'info'


# ─── Routes (Flask test client) ──────────────────────────────

@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SERVER_NAME': '127.0.0.1:5000',
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_client(app, mocker):
    mocker.patch('utils.responses.get_user_context', return_value=_user_ctx())
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['csrf_token'] = 'test_csrf_token'
    return client


@pytest.fixture
def anon_csrf_client(app):
    """Client avec CSRF token mais sans user_id."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test_csrf_token'
    return client


# ─── Conversations ───────────────────────────────────────────

class TestConversationsRoutes:

    def test_conversations_redirect_anonymous(self, client):
        resp = client.get('/conversations', follow_redirects=False)
        assert resp.status_code == 302

    def test_conversations_list(self, logged_client, mocker):
        fake_convs = [
            {'id': 1, 'cree_le': '2025-01-01', 'prenom': 'Alice', 'nom': 'K'},
            {'id': 2, 'cree_le': '2025-01-02', 'prenom': 'Bob', 'nom': 'M'},
        ]
        mocker.patch('routes.conversations.fetch_all', return_value=fake_convs)
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/conversations')
        assert resp.status_code == 200

    def test_conversations_list_db_error(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_all',
                     side_effect=Exception("DB error"))
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/conversations')
        assert resp.status_code == 500

    def test_conversation_403_not_participant(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_one', return_value=None)
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/conversations/999')
        assert resp.status_code == 403

    def test_conversation_403_on_participant_db_error(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_one',
                     side_effect=Exception("DB error"))
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/conversations/999')
        assert resp.status_code == 500

    def test_conversation_view_messages(self, logged_client, mocker):
        def mock_one(sql, params=None):
            if _has(sql, 'participants_conversation'):
                return {'existe': 1}
            return None

        fake_msgs = [
            {'id': 1, 'conversation_id': 1, 'expediteur_id': 2,
             'contenu': 'Salut!', 'prenom': 'Alice', 'nom': 'K'},
            {'id': 2, 'conversation_id': 1, 'expediteur_id': 1,
             'contenu': 'Bonjour!', 'prenom': 'Test', 'nom': 'User'},
        ]
        mocker.patch('routes.conversations.fetch_one', side_effect=mock_one)
        mocker.patch('routes.conversations.fetch_all', return_value=fake_msgs)
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/conversations/1')
        assert resp.status_code == 200

    def test_conversation_send_message(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_one',
                     return_value={'existe': 1})
        mock_exec = mocker.patch('routes.conversations.execute')

        resp = logged_client.post('/conversations/1', data={
            'contenu': 'Bonjour !',
            'csrf_token': 'test_csrf_token'
        }, follow_redirects=False)
        assert resp.status_code == 302

        mock_exec.assert_called_once()
        params = mock_exec.call_args[0][1]
        assert params == (1, 1, 'Bonjour !')

    def test_conversation_send_empty_message_renders_page(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_one',
                     return_value={'existe': 1})
        mocker.patch('routes.conversations.execute')
        mocker.patch('routes.conversations.fetch_all', return_value=[])
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.post('/conversations/1', data={
            'contenu': '   ',
            'csrf_token': 'test_csrf_token'
        })
        assert resp.status_code == 200

    def test_conversation_send_message_db_error_renders_page(self, logged_client, mocker):
        mocker.patch('routes.conversations.fetch_one',
                     return_value={'existe': 1})
        mocker.patch('routes.conversations.execute',
                     side_effect=Exception("DB error"))
        mocker.patch('routes.conversations.fetch_all', return_value=[])
        mocker.patch('routes.conversations.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.post('/conversations/1', data={
            'contenu': 'Message',
            'csrf_token': 'test_csrf_token'
        })
        assert resp.status_code == 200


# ─── Notifications ───────────────────────────────────────────

class TestNotificationsRoutes:

    def test_notifications_redirect_anonymous(self, client):
        resp = client.get('/notifications', follow_redirects=False)
        assert resp.status_code == 302

    def test_notifications_list_all(self, logged_client, mocker):
        fake_notifs = [
            {'id': 1, 'message': 'Match 1', 'type_notification': 'match_demande',
             'correspondance_id': 10, 'cree_le': '2025-01-01', 'est_lu': 0},
            {'id': 2, 'message': 'Bienvenue', 'type_notification': 'info',
             'correspondance_id': None, 'cree_le': '2025-01-02', 'est_lu': 0},
        ]
        mocker.patch('routes.notifications.fetch_all', return_value=fake_notifs)
        mock_exec = mocker.patch('routes.notifications.execute')
        mocker.patch('routes.notifications.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/notifications')
        assert resp.status_code == 200

        mock_exec.assert_called_once()
        assert _has(mock_exec.call_args[0][0], 'UPDATE notifications')

    def test_notifications_filter_match_demande(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_all', return_value=[
            {'id': 1, 'message': 'Match 1', 'type_notification': 'match_demande',
             'correspondance_id': 10, 'cree_le': '2025-01-01', 'est_lu': 0},
        ])
        mocker.patch('routes.notifications.execute')
        mocker.patch('routes.notifications.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/notifications?filtre=match_demande')
        assert resp.status_code == 200

    def test_notifications_filter_infos(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_all', return_value=[])
        mocker.patch('routes.notifications.execute')
        mocker.patch('routes.notifications.get_user_context',
                     return_value=_user_ctx())

        resp = logged_client.get('/notifications?filtre=infos')
        assert resp.status_code == 200

    def test_notifications_db_error(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_all',
                     side_effect=Exception("DB error"))

        resp = logged_client.get('/notifications')
        assert resp.status_code == 500

    def test_notifications_accept_match(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_one',
                     return_value={'correspondance_id': 42})
        mock_exec = mocker.patch('routes.notifications.execute')

        resp = logged_client.post(
            '/notifications/repondre/1/accepter',
            data={'csrf_token': 'test_csrf_token'},
            follow_redirects=False
        )
        assert resp.status_code == 302
        mock_exec.assert_called_once()
        sql = mock_exec.call_args[0][0]
        params = mock_exec.call_args[0][1]
        assert _has(sql, 'UPDATE correspondances')
        assert _has(sql, 'statut_correspondance = 1')
        assert params == (42,)

    def test_notifications_refuse_match(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_one',
                     return_value={'correspondance_id': 42})
        mock_exec = mocker.patch('routes.notifications.execute')

        resp = logged_client.post(
            '/notifications/repondre/1/refuser',
            data={'csrf_token': 'test_csrf_token'},
            follow_redirects=False
        )
        assert resp.status_code == 302
        mock_exec.assert_called_once()
        sql = mock_exec.call_args[0][0]
        assert _has(sql, 'statut_correspondance = 2')

    def test_notifications_repondre_no_correspondance(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_one',
                     return_value={'correspondance_id': None})
        mock_exec = mocker.patch('routes.notifications.execute')

        resp = logged_client.post(
            '/notifications/repondre/1/accepter',
            data={'csrf_token': 'test_csrf_token'},
            follow_redirects=False
        )
        assert resp.status_code == 302
        mock_exec.assert_not_called()

    def test_notifications_repondre_db_error(self, logged_client, mocker):
        mocker.patch('routes.notifications.fetch_one',
                     side_effect=Exception("DB error"))

        resp = logged_client.post(
            '/notifications/repondre/1/accepter',
            data={'csrf_token': 'test_csrf_token'},
            follow_redirects=False
        )
        assert resp.status_code == 500

    def test_notifications_repondre_redirect_anonymous_with_csrf(self, anon_csrf_client):
        resp = anon_csrf_client.post(
            '/notifications/repondre/1/accepter',
            data={'csrf_token': 'test_csrf_token'},
            follow_redirects=False
        )
        assert resp.status_code == 302
