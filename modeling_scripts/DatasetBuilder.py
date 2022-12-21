

class Message:
    def __init__(self, timestamp, user_id, message, mention, file_ind, uuid, uuid_parent=None, conversation_ind=None):
        self.timestamp = timestamp
        self.user = user_id
        self.message = message
        self.file_ind = file_ind
        self.uuid = uuid
        self.uuid_parent = uuid_parent
        self.conversation_ind = conversation_ind
        self.has_mention = mention > -1
        self.mention = mention

    def __lt__(self, other):
        return self.file_ind < other.file_ind

    def to_dict(self):
        return vars(self)


class MessageProcessor:
    DEFAULT_PARAMS = {
        'message_cur': '',
        'message_prev': '',
        'same_user': 0,
        'time_distance': -1,
        'mentions_user': 0,
        'label': -1
    }
    #def __init__(self):
    @staticmethod
    def process_reply_pair(message_primary, message_candidate):
        """

        :param message_primary: Message object, primary message
        :param message_candidate: Message object, potential antecedent message
        :return: modified dictionary of DEFAULT_PARAMS
        """

        results = MessageProcessor.DEFAULT_PARAMS.copy()

        results['message_cur'] = message_primary.uuid
        results['message_prev'] = message_candidate.uuid
        results['same_user'] = MessageProcessor._check_user_pair(message_primary, message_candidate)
        results['mentions_user'] = MessageProcessor._mentions_user(message_primary, message_candidate)
        results['time_distance'] = MessageProcessor._calculate_time_distance(message_primary, message_candidate)
        results['label'] = MessageProcessor._check_is_reply(message_primary, message_candidate)
        return results

    @staticmethod
    def process_same_convo(message_primary, message_candidate):

        results = MessageProcessor.DEFAULT_PARAMS.copy()

        results['message_cur'] = message_primary.uuid
        results['message_prev'] = message_candidate.uuid
        results['same_user'] = MessageProcessor._check_user_pair(message_primary, message_candidate)
        results['mentions_user'] = MessageProcessor._mentions_user(message_primary, message_candidate)
        results['time_distance'] = MessageProcessor._calculate_time_distance(message_primary, message_candidate)
        results['label'] = MessageProcessor._check_is_same_convo(message_primary, message_candidate)
        return results

    @staticmethod
    def _check_user_pair(message_primary, message_candidate):
        return int(message_primary.user == message_candidate.user)

    @staticmethod
    def _calculate_time_distance(message_primary, message_candidate):
        if message_primary.timestamp < message_candidate.timestamp:
            raise Exception(f"Primary Message {message_primary.uuid} is before candidate {message_candidate.uuid}.")
        return message_primary.timestamp - message_candidate.timestamp

    @staticmethod
    def _mentions_user(message_primary, message_candidate):
        return int(message_primary.mention == message_candidate.user)
    #Methods that generate labels
    @staticmethod
    def _check_is_reply(message_primary, message_candidate):
        return int(message_primary.uuid_parent == message_candidate.uuid)

    @staticmethod
    def _check_is_same_convo(message_primary, message_candidate):
        return int(message_primary.conversation_ind == message_candidate.conversation_ind)


class DatasetBuilder:
    def __init__(self):
        self.training_data = pd.DataFrame()
        self.labels = None
        self.size = len(self.training_data)

    def load_pair(self, data):
        """
        load single Message object
        :param message:
        :return: None
        """
        self.training_data = self.training_data.append(data, ignore_index=True)

    def load_messages(self, message_list, window=0):
        """

        :param message_list: list of Message Objects
        :return: None
        """

        if window:
            pair_list = self.pair_generator_window(message_list, window)
        else:
            pair_list = self.pair_generator(message_list)

        for pair in pair_list:
            prev_message, cur_message = pair
            data = MessageProcessor.process_same_convo(cur_message, prev_message)
            self.load_pair(data)


    @staticmethod
    def pair_generator(message_list):
        """
        Takes list of Message objects and returns a combination of all possible pairs
        :param message_list:
        :return: list of length-2 tuples
        """
        pair_list = []
        for idx, message_1 in enumerate(message_list):
            for message_2 in message_list[idx +1:]:
                if message_1 < message_2:
                    pair_list.append((message_1, message_2))
                else:
                    pair_list.append((message_2, message_1))

        return pair_list

    @staticmethod
    def pair_generator_window(message_list, window):
        """
        Takes list of Message objects and returns a combination of all possible pairs
        :param message_list:
        :return: list of length-2 tuples
        """
        pair_list = []
        for idx, message_1 in enumerate(message_list):
            for message_2 in message_list[idx+1:]:
                if message_2.timestamp - message_1.timestamp > window:
                    break
                if message_1 < message_2:
                    pair_list.append((message_1, message_2))
                else:
                    pair_list.append((message_2, message_1))
        return pair_list

    def export_data(self, path):
        self.training_data.to_csv(path)