import time

import requests


class CoupBot:

    def __init__(self, player_id, server_url):
        self.player_id = player_id
        self.server_url = server_url
        self.game_state = self._get_game_state()

    def _get_game_state(self):
        try:
            response = requests.get(f"{self.server_url}?playerId={self.player_id}")
            response.raise_for_status()
            print("Game state fetched.")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching game state: {e}")
            return None

    def _get_declarative_player(self):
        """
        Returns the player json for the player who's current turn it is.
        """
        return self.game_state["players"][self.game_state["turnIndex"]]

    def _is_my_turn(self):
        return self._get_declarative_player()['id'] == self.player_id

    def _is_action_responded(self):
        return self.player_id in self.game_state["pendingAction"]["responses"].keys()

    def _is_block_responded(self):
        return self.player_id in self.game_state["pendingAction"]["block"]["responses"].keys()

    def _is_forced_coup(self):
        return self._get_declarative_player()['coins'] >= 10

    def _determine_coup_target(self):
        for player in self.game_state["players"]:
            if player['id'] == self.player_id:
                continue

            if player['status'] == 'ACTIVE' and player['influenceCount'] > 0:
                return player['id']

        # No target found fallthrough. Should never happen.
        # TODO: Make this a better fallthrough
        return self.game_state["players"][0]['id']

    def _handle_game_state(self):
        state_type = self.game_state['phase']

        if state_type == "ACTION_DECLARATION":
            if self._is_my_turn():
                if self._is_forced_coup():
                    self._post_action(dict(action="coup", targetId=self._determine_coup_target()))
                else:
                    self._post_action(dict(action="income"))
        if state_type == "ACTION_RESPONSE":
            if not self._is_action_responded():
                self._post_action(dict(response="pass"))
        if state_type == "BLOCK_RESPONSE":
            if not self._is_block_responded():
                self._post_action(dict(response="pass"))
        if state_type == "ACTION_RESOLUTION":
            pass
        if state_type == "GAME_OVER":
            pass
        if state_type == "EXCHANGE_RESPONSE":
            # Ambassador execution special case
            if self._is_my_turn():
                self._post_action(dict(cardsToKeep=[self.game_state["pendingAction"]["exchangeOptions"][0],
                                                    self.game_state["pendingAction"]["exchangeOptions"][1]]))

    def _post_action(self, action_data):
        try:
            post_data = dict(playerId=self.player_id) | action_data
            response = requests.post(self.server_url, json=post_data)
            response.raise_for_status()
            print(f"Action posted: {post_data}")
        except requests.RequestException as e:
            print(f"Error posting action: {e}")

    def listen(self):
        while True:
            # Set game state for handling
            self.game_state = self._get_game_state()
            if self.game_state:
                self._handle_game_state()
            else:
                print("No game-state, ending bot.")
                break
            time.sleep(1)  # Prevent excessive requests
