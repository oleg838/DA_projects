import telegram
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import logging
import pandas as pd
import pandahouse
from read_db.CH import Getch
import os
sns.set



def test_report(chat=None):
    chat_id=
    bot = telegram.Bot(token='')
    data_feed = Getch('''SELECT toStartOfDay(toDateTime(time)) AS dates,
                            formatDateTime(dates, '%d/%m') as date,
                           count(DISTINCT user_id) AS DAU,
                           round(countIf(user_id, action='like')/countIf(user_id, action='view'), 3) CTR,
                           countIf(user_id, action='view') AS views,
                           countIf(user_id, action='like') AS likes
                        FROM simulator_20220320.feed_actions
                        WHERE toStartOfDay(toDateTime(time)) > yesterday() - 8
                        AND toStartOfDay(toDateTime(time)) < today()
                        GROUP BY toStartOfDay(toDateTime(time))
                        ORDER BY toStartOfDay(toDateTime(time)) ; ''').df

    data_message = Getch('''SELECT toStartOfDay(toDateTime(time)) AS dates,
                            formatDateTime(dates, '%d/%m') as date,
                            count(DISTINCT reciever_id) AS reciever
                        FROM simulator_20220320.message_actions
                        WHERE toStartOfDay(toDateTime(time)) > yesterday() - 8
                        AND toStartOfDay(toDateTime(time)) < today()
                        GROUP BY toStartOfDay(toDateTime(time))
                        ORDER BY toStartOfDay(toDateTime(time)); ''').df
    
    msg='Метрики ленты и сообщений'
    bot.sendMessage(chat_id=chat_id, text=msg)
    
    #График ленты
    
    sns.lineplot(data=data_feed, x="date", y="views")
    plt.title('Views')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'views.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    #График сообщений
    
    sns.lineplot(data=data_message, x="date", y="reciever")
    plt.title('Messages')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'recievers.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    #Файл с динамикой за день по ленте
    data = Getch('select * from simulator_20220320.feed_actions where toDate(time) = today()').df
    file_object = io.StringIO()
    data.to_csv(file_object)
    file_object.name = 'feed.csv'
    file_object.seek(0)
    bot.sendDocument(chat_id=chat_id, document=file_object)
    
    #Файл с динамикой за день по сообщениям
    
    data = Getch('select * from simulator_20220320.message_actions where toDate(time) = today()').df
    file_object = io.StringIO()
    data.to_csv(file_object)
    file_object.name = 'message.csv'
    file_object.seek(0)
    bot.sendDocument(chat_id=chat_id, document=file_object)

try:
    test_report()
except Exception as e:
    print(e)
