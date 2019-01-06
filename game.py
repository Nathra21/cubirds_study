import numpy as np
import pandas as pd
from random import shuffle

from utils import card_data
from stack import Stack, get_deck

class Game:
    def __init__(self, n_players=4):
        self.n_players = n_players
        self.current_turn = 0
        self.current_player = 0
        self.current_phase = 'lay'
        self.n_rows = 4

        self.deck = get_deck()
        self.discard = Stack()
        self.hands = self.init_hands()
        self.collections = self.init_collections()
        self.board = self.init_board()

        self.end = False
        self.winner = None

    def draw(self, n=1):
        '''Removes the first n cards from the deck and returns them.
        If draw is impossible, draws until deck is empty, then shuffles the
        discard pile into the deck.
        '''
        if len(self.deck) >= n:
            hand = self.deck.draw(n)
        else:
            if len(self.deck) + len(self.discard) >= n:
                hand = self.deck
                self.deck = self.discard
                self.discard = Stack()
                hand = hand + self.draw(n-len(hand))
            else:
                self.end_game()

        return hand

    def init_hands(self):
        hands = {}
        for player in range(self.n_players):
            hands[player] = self.draw(8)

        return hands

    def init_collections(self):
        collections = {}
        for player in range(self.n_players):
            collections[player] = self.draw(1)

        return collections

    def init_board(self):
        '''Initialize the game board with n_rows rows.
        Each row is a list of strings (not a Stack) because rows must be
        ordered.
        '''
        board = {}
        for n_row in range(self.n_rows):
            row = self.draw(3)
            while row.n_unique() < 3:
                row, dupes = row.dedupe()
                self.discard += dupes
                row += self.draw(1)
            # Now switching to a list because rows must be ordered.
            row = row.l
            shuffle(row)
            board[n_row] = row

        return board

    def complete_row(self, n_row):
        '''Complete the selected row by adding cards from the deck until at
        least two bird types are represented.
        '''
        row = self.board[n_row]
        while Stack(row).n_unique() < 2:
            row += self.draw(1).l
        self.board[n_row] = row

    def next_turn(self):
        self.current_player += 1
        if self.current_player >= self.n_players:
            self.current_player = 0
            self.current_turn += 1
        self.current_phase = 'lay'

    def next_round(self):
        '''Goes to the next round. Discards all the cards in players' hands and
        replaces them with 8 new ones.
        Resets the current player's turn (puts them back at 'lay' phase).
        '''
        self.discard += sum(self.hands)
        init_hands()
        self.current_phase = 'lay'

    def end_game(self):
        self.end = True
        if self.winner:
            print('\nThe game has ended!')
            print('The winner is: player {}!'.format(self.winner))
        else:
            print('The game has ended in a draw!')

        print('Game state at the end:\n\n')
        print(self.state_summary())

    def check_win(self, collection):
        '''Checks if a given collection is a winning one.
        There are two win conditions: having seven different species or having
        at least three of two different species.
        '''
        if collection.n_unique() >= 7:
            return True
        elif len(c for c in collection.d.values() if c >= 3) >= 2:
            return True
        else:
            return False

    def state_summary(self):
        def indent_string(s):
            return '    '+s.replace('\n', '\n    ')

        def title(s):
            return s + '\n' + '='*len(s) + '\n'

        out = [
            'Current turn: {}'.format(self.current_turn),
            'Current player: {}'.format(self.current_player),
            'Current phase: {}'.format(self.current_phase),
            '',
            'Deck:',
            indent_string(str(self.deck)),
            '\n\n'
        ]

        for player in range(self.n_players):
            out.extend([
                'Player {}:'.format(player),
                '    Hand: ' + ', '.join(self.hands[player].l),
                '    Collection: ' + ', '.join(self.collections[player].l)
            ])

        out.extend([
            '\n\n',
            'Board:'
        ])

        for n_row in range(4):
            out.append('Row {}: '.format(n_row) + ', '.join(x.rjust(8) for x in self.board[n_row]))

        return '\n'.join(out)

    def get_current_hand(self):
        return self.hands[self.current_player]
    def set_current_hand(self, value):
        self.hands[self.current_player] = value
    current_hand = property(get_current_hand, set_current_hand)

    def get_current_collection(self):
        return self.collections[self.current_player]
    def set_current_collection(self, value):
        self.collections[self.current_player] = value
    current_collection = property(get_current_collection, set_current_collection)

    def invisible(self, player):
        '''Returns the Stack of cards invisible to the given player, that is:
        cards in other players' hands or in the deck.
        '''
        return sum(self.hands) - self.current_hand + self.deck

    def visible(self, player):
        '''Returns the Stack of cards visible to the given player, that is:
        cards in his own hand, on the board, in collections or in the discard
        pile.
        '''
        return get_deck() - self.invisible(player)

    def lay(self, bird, n_row, side, draw=True):
        '''Lay all of your cards of type 'bird' on a given row and side.
        Args:
            bird (str): A valid bird type.
            n_row (int): 0-3. The row number.
            side (str): 'left' or 'right'. The side on which to lay.
            draw (bool): Whether to draw two cards from the deck if no cards are
                         taken by laying the birds.
        '''
        assert [bird] in self.current_hand, 'You do not have any {} to lay!'.format(bird)
        assert self.current_phase == 'lay', 'Now is not the time to lay birds!'

        to_lay = self.current_hand.draw_all(bird).l

        # For the sake of readability, we assume that cards are always put on
        # the right of the row. If the left is chosen, we reverse the row at the
        # start then reverse it again at the end of the process.

        row = self.board[n_row] if side == 'right' else list(reversed(self.board[n_row]))

        bird_ix = [i for i, x in enumerate(row) if x == bird]

        # If the bird is absent from the row or is present at the very right
        if (not bird_ix) or (len(row) - 1 in bird_ix):
            if draw:
                self.current_hand += self.draw(2)
        else:
            self.current_hand += row[bird_ix[-1]+1:]
            row = row[:bird_ix[-1]+1]

        row = row + to_lay
        self.board[n_row] = row if side == 'right' else list(reversed(row))
        self.complete_row(n_row)

        self.current_phase = 'flock'

    def flock(self, bird=None):
        '''Makes a flock (small or big) out of selected bird.
        '''
        assert self.current_phase == 'flock', 'Now is not the time to flock birds!'

        small = card_data[bird]['small']
        big = card_data[bird]['big']

        if bird is not None:
            n_birds = self.current_hand[bird]
            assert n_birds >= small, 'You need at least {} {}s to make a flock.'.format(small, bird)

            self.discard += self.current_hand.draw_all('parrot')
            if n_birds >= big:
                self.current_collection += [bird]*2
            else:
                self.current_collection += [bird]

        if self.check_win(self.current_collection):
            self.winner = self.current_player
            self.end_game()

        else:
            if self.current_hand.empty:
                self.next_round()
            else:
                self.next_turn()


if __name__ == '__main__':
    game = Game(n_players=2)
    # print(game.state_summary())
    game.board[0] = ['parrot', 'parrot', 'parrot', 'parrot', 'cube']
    game.hands[0] = Stack(['cube', 'cube'])
    game.lay('cube', 0, 'left')
    game.flock('parrot')
    print(game.state_summary())
