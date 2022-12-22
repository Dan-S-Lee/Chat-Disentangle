import pandas as pd


class ConversationBuilder:
    @staticmethod
    def filter_nulls(df):
        """

        :param df: dataframe with parent, child, uuid columns.
        :return:
        """
        labeled_df = df[(df["parent"].notnull()) | (df["child"].notnull())]
        labeled_df = labeled_df.set_index("uuid")
        labeled_df = labeled_df[labeled_df['uuid_parent'].notnull()]
        return labeled_df

    @staticmethod
    def add_messages(conversation, child, parent):
        """
        :param conversation: set of UUIDs
        :param child: uuid of primary message being evaluated
        :param parent: uuid of child's antecedent (message it's replying to)
        :return: conversation: modified set of uuids with the child and parent added
        """
        conversation.add(child)
        conversation.add(parent)
        return conversation

    @staticmethod
    def extract_conversation_uuids(df):
        """
        :param df:
        :return: conversations: list of sets of UUIDs, sets contain a full conversation
        """

        # List of conversations (list of sets)
        conversations = list()
        for ind, row in df.iterrows():
            found = False
            for con in conversations:
                if (row["uuid_parent"] in con or ind in con):
                    ConversationBuilder.add_messages(con, row['uuid_parent'], ind)
                    found = True
                    break
            if not conversations or not found:
                conversations.append(ConversationBuilder.add_messages(set(), ind, row['uuid_parent']))

        print(len(conversations), "conversations extracted.")
        return conversations

    @staticmethod
    def detangle(filepath):
        """
        Read csv, filter, extract conversation uuids
        :param filepath:
        :return: list dataframes
        """
        raw_df = pd.read_csv(filepath, index_col=0)
        labeled_df = ConversationBuilder.filter_nulls(raw_df)
        conversations = ConversationBuilder.extract_conversation_uuids(labeled_df)

        df_list = []
        for con in conversations:
            if not con:
                continue
            df = labeled_df.loc[list(con)].copy()
            df_list.append(df)
        return df_list


if __name__ == '__main__':
    filepath = "../data/cleaned/agg_train.csv"
    df_list = ConversationBuilder.detangle(filepath)
    print(len(df_list))

    df_list[0].sort_values(by='file_ind')
    # %%
    full_df = pd.DataFrame(columns=list(df_list[0].columns.values) + ['conversation_ind'])
    for i, df in enumerate(df_list):
        temp_df = df.copy()
        temp_df['conversation_ind'] = i
        temp_df = temp_df.sort_values(by=['date', 'file_ind'])
        full_df = pd.concat([full_df, temp_df])
    full_df = full_df.drop_duplicates()
    full_df.to_csv('../cleaned/train_conversations.csv')

