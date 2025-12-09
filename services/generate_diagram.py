import matplotlib.pyplot as plt


def generate_diagram(tandem_id, completed_challenges, max_challenges=204): #1205 было 27, +4 = 31. Почему-то у них макс балл 30, значит что-то я недобавил
    labels = ['Выполнено', 'Всего челленджей']
    #print('COMPLETED CHALLENGES ', completed_challenges, '\nMAX_CHALLENGES  ', max_challenges)
    sizes = [completed_challenges, max_challenges - completed_challenges]
    colors = ['#FDCD07', '#2277BC']
    explode = (0.05, 0)


    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=50,
        colors=colors,
        explode=explode,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 10, 'color': 'black'}
    )


    ax.set_title('Прогресс по челленджам', fontsize=16, fontweight='bold')
    plt.setp(autotexts, size=12, weight='bold')
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig(f'diagrams/{tandem_id}.png')
