[![CI](https://github.com/terminalkitten/django-insights/actions/workflows/main.yml/badge.svg)](https://github.com/terminalkitten/django-insights/actions/workflows/main.yml)

!["Django Insights"](https://raw.githubusercontent.com/terminalkitten/django-insights/main/docs/assets/images/banner.png)

## Features

Create insights for your app, store them in a SQLite database for further processing, these insights are written right next to your application logic.

## Note:

Still working on some small things and making and extented tests and docs will follow soon.
For now focus is on:

- Django 3.2 (LTS), 4.0,4.1 and 4.2;
- Python ≥ 3.8

## Installation

Installing with:

```bash
pip install 'django-insights'
```

## Usage

First create 1 or more `insights.py` file(s) in your app directory, for example:

```bash
project
└── testapp
    └── insights.py
```

In these insights files your write out any metric you would like to track. Eacht metric starts with a question and some values to store. Below is a example of the `@metrics.counter` function:

```python
# project/testapp/insights.py
from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()

```

Add django_insights package, insights database and router to your settings

```python

INSTALLED_APPS = [
    ...
    "django_insights",
]


DATABASES = {
    ...
    "insights": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db/insights.db"},
    ...
}

DATABASE_ROUTERS = ['django_insights.database.Router']

```

Note: please make sure you exclude the database in your `.gitignore` file

Migrate insights database:

```bash
workon myapp
python manage.py migrate insights --database=insights
```

Now collect your insights

```bash
python manage.py collect_insights
```

You now have a database containing all insights from your application.
You can inspect this database yourself with `sqlite3 db/insights.db` - or - you can use the Django Insights dashboard.

To enable this dashboard, add the following settings:

```python
from django.urls import include, path

urlpatterns = [
    path(
        '/insights',
        include('django_insights.urls', namespace='insights'),
    ),
]
```

Now you can visit https://localhost:8000/insights to inspect your Django Insights database

Django insights contains 5 types of metrics it can collect:

- counter
- gauge
- timeseries
- scatterplot
- barchart

### Counter:

```python
from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()

```

### Gauge:

```python

from django.db.models import Avg, Count

from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.gauge(question="Average book(s) per author?")
def avg_books_per_author() -> int:
    avg_total_books = (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .aggregate(Avg('total_books'))
        .get('total_books__avg')
    )

    return avg_total_books
```

### Timeseries:

```python
from datetime import datetime

from django.db.models import Count
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from project.testapp.models import Book


@metrics.timeseries(
    question="Num of books created per month?",
    desc="How many books are added each month, since the opening of our store",
    xlabel="Month",
    xformat='%m',
    ylabel="Num of books",
)
def num_of_books_per_month() -> list[tuple[datetime, int]]:
    return (
        Book.objects.all()
        .annotate(month=TruncMonth('created'))
        .values('month')
        .filter(month__isnull=False)
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )
```

### Scatterplot:

```python
from datetime import datetime

from django.db.models import Count, Value

from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.scatterplot(
    question="Num of books by age of author?",
    xlabel="Age",
    ylabel="Num of books",
)
def author_age_vs_num_of_books() -> list[tuple[float, float, Any]]:
    return (
        Author.objects.values('age')
        .annotate(num_of_books=Count('books'), category=Value("author"))
        .values_list('num_of_books', 'age', 'category')
    )
```

### Barchart:

```python
from datetime import datetime

from django.db.models import Case, Count, Value, When

from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.barchart(
    question="Num of books by gender of author?",
    xlabel="Gender",
    ylabel="Num of books",
)
def author_gender_vs_num_of_books() -> list[tuple[float, float, str]]:
    return (
        Author.objects.values('gender')
        .annotate(
            num_of_books=Count('books'),
            gender_category=Case(
                When(gender=1, then=Value('Male')),
                When(gender=2, then=Value('Female')),
            ),
        )
        .values_list('num_of_books', 'gender', 'gender_category')
    )

```

## Settings

```python
# Custom app name
INSIGHTS_APP_NAME = "Bezamon"

# Menu translation
INSIGHTS_MENU = {'project.testapp.insights': 'Books'}

# Quality of chart images
INSIGHTS_CHART_DPI = 180

# Change primary color
INSIGHTS_CHART_PRIMARY_COLOR = "#336699"
```

## Background

I'm currently working at a small company that is in the process of renewing some parts of our product. To gain insight into the usage over different periods, we have tried a few solutions. We initially attempted to periodically generate CSV files from queries, as well as send data to a dashboard at regular intervals.

We ended up with many exports that where spread out over multiple people. Additionally, exporting data directly from the database also posed a security risk, as it required constant movement of possible sensitive information. After several months of working with CSV files, which were often outdated and required conversion by other (paid) tools, we where looking for a better solution.

I wanted an easy-to-configure file within our various apps that would allow me to create "insights" easily, so Django Insights was born. I decided to switch to a local SQLite database which could be share on request, as a plus these files can be tracked by a security officer.

## Documentation

Write more about where to find documentation

## Ideas

- Connect to other datasources and export to different file-formats ( ArrowFile?, NDJSON )

## Is it any good?

[Yes.](http://news.ycombinator.com/item?id=3067434)

## License

The MIT License
