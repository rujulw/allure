from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.game.deck import Card, Deck
from app.game.evaluator import HandEvaluator
from app.game.pot import PotCalculator
from app.game.state import Action, ActionType, HandState, LegalAction, Phase, PlayerState, Street


class GameEngine:
    def __init__(
        self,
        players: Sequence[tuple[str, int]],
        *,
        dealer_index: int = 0,
        small_blind: int = 50,
        big_blind: int = 100,
        deck: Deck | None = None,
    ):
        if len(players) < 2:
            raise ValueError("Texas Hold'em requires at least two players")
        if small_blind <= 0 or big_blind <= 0 or small_blind > big_blind:
            raise ValueError("Blind structure is invalid")

        self.player_templates = list(players)
        self.dealer_index = dealer_index % len(players)
        self.small_blind = small_blind
        self.big_blind = big_blind
        self._deck = deck
        self._hand_counter = 0
        self.state: HandState | None = None

    def start_hand(self) -> HandState:
        players = [
            PlayerState(player_id=player_id, seat_index=index, stack=stack)
            for index, (player_id, stack) in enumerate(self.player_templates)
        ]
        active_players = [player for player in players if player.stack > 0]
        if len(active_players) < 2:
            raise ValueError("Need at least two funded players to start a hand")

        self._hand_counter += 1
        dealer = players[self.dealer_index]
        dealer.is_dealer = True

        deck_cards = list((self._deck or self._fresh_deck()).cards)
        state = HandState(
            hand_id=self._hand_counter,
            phase=Phase.BETTING,
            street=Street.PREFLOP,
            dealer_index=self.dealer_index,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            players=players,
            deck=deck_cards,
            last_full_raise=self.big_blind,
        )

        self._deal_hole_cards(state)
        small_blind_index, big_blind_index = self._blind_positions(state)
        self._mark_blinds(state, small_blind_index, big_blind_index)
        self._post_forced_bet(state.players[small_blind_index], state.small_blind)
        self._post_forced_bet(state.players[big_blind_index], state.big_blind)

        state.current_bet = max(player.current_bet for player in state.players)
        state.pot = self._total_pot(state)
        state.pots = PotCalculator.build_pots(state.players)

        if len(state.players) == 2:
            state.current_actor_index = small_blind_index
        else:
            state.current_actor_index = self._next_eligible_player_index(big_blind_index, state)

        state.legal_actions = self.legal_actions(state)
        self.state = state
        return state

    def legal_actions(self, state: HandState | None = None) -> list[LegalAction]:
        current_state = state or self.state
        if current_state is None or current_state.phase != Phase.BETTING:
            return []

        actor = current_state.current_actor
        if actor is None or not actor.can_act:
            return []

        amount_to_call = max(current_state.current_bet - actor.current_bet, 0)
        max_total = actor.current_bet + actor.stack
        actions: list[LegalAction] = []

        if amount_to_call > 0:
            actions.append(LegalAction(ActionType.FOLD, call_amount=amount_to_call))
            if actor.stack >= amount_to_call:
                actions.append(LegalAction(ActionType.CALL, call_amount=amount_to_call))
        else:
            actions.append(LegalAction(ActionType.CHECK))

        min_raise_to = self._min_raise_to(current_state, actor)
        if actor.stack > amount_to_call and min_raise_to is not None and max_total >= min_raise_to:
            actions.append(
                LegalAction(
                    ActionType.RAISE,
                    min_amount=min_raise_to,
                    max_amount=max_total,
                    call_amount=amount_to_call,
                )
            )

        if actor.stack > 0:
            actions.append(LegalAction(ActionType.ALL_IN, amount=max_total, call_amount=amount_to_call))

        return actions

    def apply_action(self, action: Action) -> HandState:
        if self.state is None:
            raise RuntimeError("No hand is active")
        state = self.state
        if state.phase != Phase.BETTING:
            raise ValueError("Hand is not accepting actions")

        actor = state.current_actor
        if actor is None or actor.player_id != action.player_id:
            raise ValueError("Action does not match the current actor")

        state.legal_actions = self.legal_actions(state)
        self._validate_action(state, actor, action)

        amount_to_call = max(state.current_bet - actor.current_bet, 0)
        previous_current_bet = state.current_bet

        if action.action_type == ActionType.FOLD:
            actor.folded = True
            actor.has_acted = True
        elif action.action_type == ActionType.CHECK:
            actor.has_acted = True
        elif action.action_type == ActionType.CALL:
            self._commit_bet(actor, amount_to_call)
            actor.has_acted = True
        elif action.action_type in (ActionType.RAISE, ActionType.ALL_IN):
            target_bet = action.amount if action.action_type == ActionType.RAISE else actor.current_bet + actor.stack
            if target_bet is None:
                raise ValueError("Raise actions require a target amount")
            contribution = target_bet - actor.current_bet
            self._commit_bet(actor, contribution)
            actor.has_acted = True
            if target_bet > state.current_bet:
                raise_size = target_bet - state.current_bet
                state.current_bet = target_bet
                if raise_size >= state.last_full_raise:
                    state.last_full_raise = raise_size
                for player in state.players:
                    if player.player_id == actor.player_id or player.folded or player.all_in:
                        continue
                    if player.current_bet < state.current_bet:
                        player.has_acted = False
        else:
            raise ValueError(f"Unsupported action: {action.action_type}")

        actor.last_action = action.action_type
        state.action_history.append(action)
        state.pot = self._total_pot(state)
        state.pots = PotCalculator.build_pots(state.players)

        remaining = [player for player in state.players if not player.folded]
        if len(remaining) == 1:
            self._award_uncontested_pot(state, remaining[0])
            return state

        if self._betting_round_complete(state):
            self._advance_street(state)
            return state

        if state.current_bet != previous_current_bet:
            state.pots = PotCalculator.build_pots(state.players)

        next_actor_index = self._next_eligible_player_index(actor.seat_index, state)
        if next_actor_index is None:
            self._advance_street(state)
            return state

        state.current_actor_index = next_actor_index
        state.legal_actions = self.legal_actions(state)
        return state

    def _advance_street(self, state: HandState) -> None:
        if state.street == Street.RIVER:
            self._run_showdown(state)
            return

        if state.street == Street.PREFLOP:
            state.street = Street.FLOP
            state.community_cards.extend(self._draw_cards(state, 3))
        elif state.street == Street.FLOP:
            state.street = Street.TURN
            state.community_cards.extend(self._draw_cards(state, 1))
        elif state.street == Street.TURN:
            state.street = Street.RIVER
            state.community_cards.extend(self._draw_cards(state, 1))
        else:
            raise ValueError(f"Cannot advance from street {state.street}")

        state.current_bet = 0
        state.last_full_raise = state.big_blind
        for player in state.players:
            player.current_bet = 0
            player.has_acted = False

        if self._should_fast_forward(state):
            self._fast_forward_to_showdown(state)
            return

        state.current_actor_index = self._first_postflop_actor_index(state)
        state.legal_actions = self.legal_actions(state)
        state.pots = PotCalculator.build_pots(state.players)
        state.pot = self._total_pot(state)

    def _run_showdown(self, state: HandState) -> None:
        state.phase = Phase.SHOWDOWN
        state.street = Street.SHOWDOWN
        state.current_actor_index = None
        state.legal_actions = []
        state.pot = self._total_pot(state)
        state.pots = PotCalculator.build_pots(state.players)

        contenders = {
            player.player_id: HandEvaluator.evaluate(player.hole_cards + state.community_cards)
            for player in state.players
            if not player.folded
        }
        payouts = {player.player_id: 0 for player in state.players}
        winners: set[str] = set()

        for pot in state.pots:
            eligible = [player for player in state.players if player.player_id in pot.eligible_player_ids]
            if not eligible:
                continue
            best_hand = max(contenders[player.player_id].comparison_key for player in eligible)
            pot_winners = [player for player in eligible if contenders[player.player_id].comparison_key == best_hand]
            share = pot.amount // len(pot_winners)
            remainder = pot.amount % len(pot_winners)
            ordered_winners = self._seat_order_from(state.dealer_index, state)
            ordered_winners = [index for index in ordered_winners if state.players[index] in pot_winners]

            for winner in pot_winners:
                payouts[winner.player_id] += share
                winners.add(winner.player_id)
            for index in ordered_winners[:remainder]:
                payouts[state.players[index].player_id] += 1

        for player in state.players:
            payout = payouts[player.player_id]
            player.stack += payout
            player.winnings += payout

        state.payouts = payouts
        state.winner_ids = sorted(winners)
        state.phase = Phase.COMPLETE

    def _award_uncontested_pot(self, state: HandState, winner: PlayerState) -> None:
        state.phase = Phase.COMPLETE
        state.current_actor_index = None
        state.legal_actions = []
        state.pot = self._total_pot(state)
        state.pots = PotCalculator.build_pots(state.players)
        winner.stack += state.pot
        winner.winnings += state.pot
        state.payouts = {player.player_id: 0 for player in state.players}
        state.payouts[winner.player_id] = state.pot
        state.winner_ids = [winner.player_id]

    def _fast_forward_to_showdown(self, state: HandState) -> None:
        while len(state.community_cards) < 5:
            state.community_cards.extend(self._draw_cards(state, 1 if state.street != Street.PREFLOP else 3))
            if state.street == Street.PREFLOP:
                state.street = Street.FLOP
            elif state.street == Street.FLOP:
                state.street = Street.TURN
            elif state.street == Street.TURN:
                state.street = Street.RIVER
        self._run_showdown(state)

    def _deal_hole_cards(self, state: HandState) -> None:
        deal_order = self._seat_order_from(state.dealer_index, state)
        for _ in range(2):
            for index in deal_order:
                player = state.players[index]
                if player.stack > 0:
                    player.hole_cards.extend(self._draw_cards(state, 1))

    def _post_forced_bet(self, player: PlayerState, amount: int) -> None:
        contribution = min(player.stack, amount)
        self._commit_bet(player, contribution)
        player.has_acted = False

    @staticmethod
    def _commit_bet(player: PlayerState, contribution: int) -> None:
        if contribution < 0 or contribution > player.stack:
            raise ValueError("Contribution is invalid")
        player.stack -= contribution
        player.current_bet += contribution
        player.total_committed += contribution
        if player.stack == 0:
            player.all_in = True

    def _validate_action(self, state: HandState, actor: PlayerState, action: Action) -> None:
        available = {entry.action_type: entry for entry in state.legal_actions}
        if action.action_type not in available:
            raise ValueError(f"Illegal action for current actor: {action.action_type}")

        if action.action_type == ActionType.CHECK and state.current_bet != actor.current_bet:
            raise ValueError("Cannot check while facing a bet")
        if action.action_type == ActionType.CALL and actor.stack < state.current_bet - actor.current_bet:
            raise ValueError("Call exceeds remaining stack; use all-in")
        if action.action_type == ActionType.RAISE:
            legal_raise = available[ActionType.RAISE]
            if action.amount is None:
                raise ValueError("Raise action requires an amount")
            if legal_raise.min_amount is None or legal_raise.max_amount is None:
                raise ValueError("Raise bounds are missing")
            if action.amount < legal_raise.min_amount or action.amount > legal_raise.max_amount:
                raise ValueError("Raise amount is outside legal bounds")
        if action.action_type == ActionType.ALL_IN and actor.stack <= 0:
            raise ValueError("Player has no chips left to move all-in")

    def _betting_round_complete(self, state: HandState) -> bool:
        remaining = [player for player in state.players if not player.folded]
        if len(remaining) <= 1:
            return True

        actionable = [player for player in remaining if not player.all_in]
        if not actionable:
            return True

        for player in actionable:
            if player.current_bet != state.current_bet:
                return False
            if not player.has_acted:
                return False
        return True

    def _should_fast_forward(self, state: HandState) -> bool:
        active = [player for player in state.players if not player.folded and not player.all_in]
        return len(active) <= 1

    def _first_postflop_actor_index(self, state: HandState) -> int | None:
        return self._next_eligible_player_index(state.dealer_index, state)

    def _next_eligible_player_index(self, start_index: int, state: HandState) -> int | None:
        total_players = len(state.players)
        for offset in range(1, total_players + 1):
            candidate = state.players[(start_index + offset) % total_players]
            if candidate.can_act:
                return candidate.seat_index
        return None

    def _blind_positions(self, state: HandState) -> tuple[int, int]:
        if len(state.players) == 2:
            small_blind_index = state.dealer_index
            big_blind_index = self._next_seat(state.dealer_index, state)
            return small_blind_index, big_blind_index

        small_blind_index = self._next_seat(state.dealer_index, state)
        big_blind_index = self._next_seat(small_blind_index, state)
        return small_blind_index, big_blind_index

    def _mark_blinds(self, state: HandState, small_blind_index: int, big_blind_index: int) -> None:
        state.players[small_blind_index].is_small_blind = True
        state.players[big_blind_index].is_big_blind = True

    @staticmethod
    def _draw_cards(state: HandState, count: int) -> list[Card]:
        if count > len(state.deck):
            raise ValueError("Not enough cards remaining in deck")
        dealt = state.deck[:count]
        del state.deck[:count]
        return dealt

    @staticmethod
    def _next_seat(index: int, state: HandState) -> int:
        return (index + 1) % len(state.players)

    @staticmethod
    def _fresh_deck() -> Deck:
        deck = Deck()
        deck.shuffle()
        return deck

    @staticmethod
    def _seat_order_from(start_index: int, state: HandState) -> list[int]:
        total = len(state.players)
        return [((start_index + offset) % total) for offset in range(1, total + 1)]

    @staticmethod
    def _total_pot(state: HandState) -> int:
        return sum(player.total_committed for player in state.players)

    @staticmethod
    def _min_raise_to(state: HandState, actor: PlayerState) -> int | None:
        amount_to_call = max(state.current_bet - actor.current_bet, 0)
        if actor.stack <= amount_to_call:
            return None
        if state.current_bet == 0:
            return actor.current_bet + state.big_blind
        return state.current_bet + state.last_full_raise
