from django.shortcuts import render

# Create your views here.
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic import UpdateView
from django.views.generic.edit import CreateView, FormView
from django.views.generic.dates import YearArchiveView, MonthArchiveView
from blog.models import Article, Category, Tag
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from comments.forms import CommentForm
from django.conf import settings
from django import forms
from django import http
from django.http import HttpResponse
from abc import ABCMeta, abstractmethod
from haystack.generic_views import SearchView
from blog.forms import BlogSearchForm
import datetime
from django.views.decorators.csrf import csrf_exempt
import os
from django.contrib.auth.decorators import login_required

"""
class SeoProcessor():
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_title(self):
        pass

    @abstractmethod
    def get_keywords(self):
        pass

    @abstractmethod
    def get_description(self):
        pass
"""


class ArticleListView(ListView):
    # template_name属性用于指定使用哪个模板进行渲染
    template_name = 'blog/article_index.html'

    # context_object_name属性用于给上下文变量取名（在模板中使用该名字）
    context_object_name = 'article_list'

    # 页面类型，分类目录或标签列表等
    page_type = ''
    paginate_by = settings.PAGINATE_BY
    page_kwarg = 'page'


class IndexView(ArticleListView):
    def get_queryset(self):
        article_list = Article.objects.filter(type='a', status='p')

        # for article in article_list:
        #     article.body = article.body[0:settings.ARTICLE_SUB_LENGTH]
        #     # article.body = markdown2.markdown(article.body)

        return article_list


class ArticleDetailView(DetailView):
    template_name = 'blog/article_detail.html'
    model = Article
    pk_url_kwarg = 'article_id'
    context_object_name = "article"

    def get_object(self):
        obj = super(ArticleDetailView, self).get_object()
        obj.viewed()
        # obj.body = markdown2.markdown(obj.body)
        self.object = obj
        return obj

    def get_context_data(self, **kwargs):
        articleid = int(self.kwargs[self.pk_url_kwarg])

        comment_form = CommentForm()
        u = self.request.user

        if self.request.user.is_authenticated:
            comment_form.fields.update({
                'email': forms.CharField(widget=forms.HiddenInput()),
                'name': forms.CharField(widget=forms.HiddenInput()),
            })
            user = self.request.user
            comment_form.fields["email"].initial = user.email
            comment_form.fields["name"].initial = user.username

        article_comments = self.object.comment_set.all()

        kwargs['form'] = comment_form
        kwargs['article_comments'] = article_comments
        kwargs['comment_count'] = len(article_comments) if article_comments else 0;

        kwargs['next_article'] = self.object.next_article
        kwargs['prev_article'] = self.object.prev_article

        return super(ArticleDetailView, self).get_context_data(**kwargs)

    """
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            pass
    """


'''
class PageDetailView(ArticleDetailView):
    model = BlogPage
    pk_url_kwarg = 'page_id'

    def get_object(self):
        obj = super(PageDetailView, self).get_object()
        print(obj.title)
        obj.viewed()
        # obj.body = markdown2.markdown(obj.body)
        return obj
'''


class CategoryDetailView(ArticleListView):
    # template_name = 'article_index.html'
    # context_object_name = 'article_list'

    # pk_url_kwarg = 'article_name'
    page_type = "分类目录归档"

    def get_queryset(self):
        categoryname = self.kwargs['category_name']

        try:
            categoryname = categoryname.split('/')[-1]
        except:
            pass
        article_list = Article.objects.filter(category__name=categoryname, status='p')
        return article_list

    def get_context_data(self, **kwargs):
        categoryname = self.kwargs['category_name']
        try:
            categoryname = categoryname.split('/')[-1]
        except:
            pass
        kwargs['page_type'] = CategoryDetailView.page_type
        kwargs['tag_name'] = categoryname
        return super(CategoryDetailView, self).get_context_data(**kwargs)


class AuthorDetailView(ArticleListView):
    page_type = '作者文章归档'

    def get_queryset(self):
        author_name = self.kwargs['author_name']

        article_list = Article.objects.filter(author__username=author_name)
        return article_list

    def get_context_data(self, **kwargs):
        author_name = self.kwargs['author_name']
        kwargs['page_type'] = AuthorDetailView.page_type
        kwargs['tag_name'] = author_name
        return super(AuthorDetailView, self).get_context_data(**kwargs)


class TagListView(ListView):
    template_name = ''
    context_object_name = 'tag_list'

    def get_queryset(self):
        tags_list = []
        tags = Tag.objects.all()
        for t in tags:
            t.article_set.count()


class TagDetailView(ArticleListView):
    page_type = '分类标签归档'

    def get_queryset(self):
        tag_name = self.kwargs['tag_name']

        article_list = Article.objects.filter(tags__name=tag_name)
        return article_list

    def get_context_data(self, **kwargs):
        tag_name = self.kwargs['tag_name']
        kwargs['page_type'] = TagDetailView.page_type
        kwargs['tag_name'] = tag_name
        return super(TagDetailView, self).get_context_data(**kwargs)


@csrf_exempt
def fileupload(request):
    if request.method == 'POST':
        fname = ''
        timestr = datetime.datetime.now().strftime('%Y/%m/%d')
        basepath = os.path.join(r'/var/www/resource/image/', timestr)
        if not os.path.exists(basepath):
            os.makedirs(basepath)
        fname = ''
        for filename in request.FILES:
            fname = filename
            savepath = os.path.join(basepath, filename)
            with open(savepath, 'wb+') as wfile:
                for chunk in request.FILES[filename].chunks():
                    wfile.write(chunk)
        return HttpResponse('https://resource.lylinux.net/' + 'image/' + timestr + '/' + fname)

    else:
        return HttpResponse("only for post")


@login_required
def refresh_memcache(request):
    try:
        if request.user.is_superuser:
            result = os.popen(' service memcached restart ').readline()
            return HttpResponse(result)
        else:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
    except Exception as e:
        return HttpResponse(e);


"""
class BlogSearchView(SearchView):
    form_class = BlogSearchForm
    template_name = 'blog/article_detail.html'
    model = Article
    # template_name属性用于指定使用哪个模板进行渲染
    template_name = 'blog/article_index.html'

    # context_object_name属性用于给上下文变量取名（在模板中使用该名字）
    context_object_name = 'article_list'

    def get_queryset(self):
        queryset = super(BlogSearchView, self).get_queryset()
        # further filter queryset based on some set of criteria
        # return queryset.filter(pub_date__gte=date(2015, 1, 1))
        return queryset

    def get_context_data(self, **kwargs):
        tag_name = 'search'
        kwargs['page_type'] = 'search'
        kwargs['tag_name'] = tag_name
        return super(BlogSearchView, self).get_context_data(**kwargs)
"""
