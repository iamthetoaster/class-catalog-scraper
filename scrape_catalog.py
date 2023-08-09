#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from itertools import chain

 # TODO: This is very messy.

class Course:
    def __init__(self, code, name, url, prereq_codes):
        self.code = code
        self.name = name
        self.url = url
        self.prereq_codes = prereq_codes

    def describe_node(self):
        print(f'"{self.code}" [tooltip="{self.name}" href="{self.url}"]')

    def describe_prereqs(self):
        for prereq in self.prereq_codes:
            print(f'"{prereq}" -> "{self.code}"')

# Departments from Catalog
def departments_from_catalog_url(url, base_url=None):
    if base_url is None:
        uri = urlparse(url)
        base_url = f"{uri.scheme}://{uri.netloc}"

    page = requests.get(URL.lower())

    soup = BeautifulSoup(page.content, "html.parser")

    department_soup = soup.find("ul", class_="sc-child-item-links").find_all("a")
    # TODO: make department type probably? return dict of codes to department objects
    departments = dict()
    for department in department_soup:
        [code, name] = re.split('\s*-\s*' , department.text)
        link = f"{base_url}{department['href']}"

        departments[code] = (name, link)
    return departments

def courses_from_department_url(url, base_url=None, courses=None, predicate=None, recurse=False, loud=False):
    if courses is None:
        courses = dict()
    page = requests.get(url.lower())
    if base_url is None:
        uri = urlparse(url)
        base_url = f"{uri.scheme}://{uri.netloc}"
    soup = BeautifulSoup(page.content, "html.parser")
    courses_soup = soup.find_all("h2", class_= "course-name")
    for course in courses_soup:
        code = course.find("span").text
        course.find("span").replace_with('')
        name = course.text.strip()
        link = f"{base_url}{course.find('a')['href']}"
        if predicate is None or predicate(code, name):
            courses[code] = course_from_url(link, courses=courses, recurse=recurse, loud=loud)
    return courses

def course_from_url(url, base_url=None, courses=None, recurse=False, loud=False):
    page = requests.get(url.lower())
    if base_url is None:
        uri = urlparse(url)
        base_url = f"{uri.scheme}://{uri.netloc}"
    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup.prettify())
    course_soup = soup.find(id="main")
    header = course_soup.find("h1")
    code = header.find("span", class_=None).text
    if loud:
        print(code)
    if courses is not None and code not in courses:
        courses[code] = None

    for span in header.find_all("span"):
        span.replace_with('')
    name = header.text.strip()
    extra_fields = course_soup.find_all("div", class_="extraFields")
    prereq_soup = chain.from_iterable(map(lambda item: item.find_all("a", class_="sc-courselink"), extra_fields))
    prereq_codes = []
    for prereq in prereq_soup:
        prereq_code = prereq.text.strip()
        prereq_codes.append(prereq_code)
        if recurse and (courses is None or prereq_code not in courses):
            course_from_url(f"{base_url}{prereq['href']}", base_url=base_url, courses=courses, recurse=recurse, loud=loud)
    result = Course(code, name, url, prereq_codes)
    if courses is not None:
        courses[code] = result
    return result

def parse_course_code(code):
    [department, number] = code.split()
    return int(re.search("[0-9]+", number).group())
