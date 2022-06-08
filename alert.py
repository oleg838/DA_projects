import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse
from datetime import date
import io
from read_db.CH import Getch
import sys
import os


def check_anomaly(df, metric, a=4, n=5):
    df['q25'] = df[metric].shift(1).rolling(n).quantile(0.25)
    df['q75'] = df[metric].shift(1).rolling(n).quantile(0.75)
    df['iqr'] = df['q75'] - df['q25']
    df['up'] = df['q75'] + a*df['iqr']
    df['low'] = df['q25'] - a*df['iqr']
    
    df['up'] = df['up'].rolling(n, center=True, min_periods=1).mean()
    df['low'] = df['low'].rolling(n, center=True, min_periods=1).mean()
    
    if df[metric].iloc[-1] < df['low'].iloc[-1] or df[metric].iloc[-1] > df['up'].iloc[-1]:
        is_alert = 1
    else:
        is_alert = 0
        
    return is_alert, df
    
def run_alerts(chat=None):
    chat_id=chat_id
    bot = telegram.Bot(token='token_place')

    # для удобства построения графиков в запрос можно добавить колонки date, hm
    data = Getch(''' SELECT
                          toStartOfFifteenMinutes(time) as ts
                        , toDate(ts) as date
                        , formatDateTime(ts, '%R') as hm
                        , uniqExact(user_id) as users_feed
                        , countIf(user_id, action='view') as views
                        , countIf(user_id, action='like') as likes
                    FROM db_name
                    WHERE ts >=  today() - 1 and ts < toStartOfFifteenMinutes(now())
                    GROUP BY ts, date, hm
                    ORDER BY ts ''').df
    print(data)
    
    metrics_list = ['users_feed','views','likes']
    for metric in metrics_list:
        print(metric)
        df = data[['ts','date','hm',metric]].copy()
        is_alert, df = check_anomaly(df,metric)

        if is_alert==1:
            msg = '''Метрика {metric}:\nтекущее значение = {current_value:.2f}\nотклонение от вчера {diff:.2%}'''.format(metric=metric,
                                                                                                                         current_value=df[metric].iloc[-1],
                                                                                                                        diff=(df[metric].iloc[-1]/df[metric].iloc[-2]))
            sns.set(rc={'figure.figsize' : (16,10)})
            plt.tight_layout()

            ax = sns.lineplot(x=df['ts'], y=df[metric], label = 'metric')
            ax = sns.lineplot(x=df['ts'], y=df['up'], label = 'up')
            ax = sns.lineplot(x=df['ts'], y=df['low'], label = 'low')

            for ind, label in enumerate(ax.get_xticklabels()):
                if ind % 2 == 0:
                    label.set_visible(True)
                else:
                    label.set_visible(False)
                
            ax.set(xlabel='time')
            ax.set(ylabel=metric)

            ax.set_title(metric)
            ax.set(ylim=(0, None))

            plot_object = io.BytesIO()
            ax.figure.savefig(plot_object)
            plot_object.seek(0)
            plot_object.name = '{0}.png'.format(metric)
            plt.close()

            bot.sendMessage(chat_id=chat_id, text=msg)
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
run_alerts()
