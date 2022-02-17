import requests
import os.path
import dateutil.parser as dparser
import datetime
import csv
import json

REQUREST_URL = 'https://workat.tech/api/jobs/'
IMAGE_PREFIX_URL = "https://d2yjqys1j7uhg1.cloudfront.net"
CSV_FILE_REL_PATH = "./Files/ScrapedJobs.csv"


# Expiry offset of days
EXPIRY_OFFSET = 30
OPPORTUNITY_OFFSET = 1

# Keys from api response
ID = "id"
LOGO = "logo"
TITLE = "title"
TYPE = "type"
DEPARTMENT = "department"
LOCATIONS = "locations"
DATE_POSTED = "date_posted"
EXTERNAL_URL = "externalUrl"
EXPERIENCE = "experience"
MIN = "min"
MAX = "max"
LEVEL = "level"
COMPANY = "company"
NAME = "name"
SKILLS = "skills"
JOB_DESCRIPTION = "job_description"

'''
Fields in Firestore -->
    companyName - string
	createdOn - timestamp
	expiresOn - timestamp
	imageLink - string
	jobDescription - string
	jobLink - string
	location - string
	opportunityDate - timestamp
	requiredExperience - string
	role - string
	updatedOn - timestamp
'''

COLUMN_HEADERS = list(["companyName", "createdOn", "expiresOn", "imageLink", "jobDescription",
                      "jobLink", "location", "opportunityDate", "requiredExperience", "role", "updatedOn"])
LOCATIONS_LIST = list(["GURUGRAM", "HYDERABAD", "BENGALURU",
                      "NOIDA", "PUNE", "MUMBAI", "REMOTE", "DELHI", "CHENNAI"])


def getRowFromJobFields(jobFields):
    date_posted_datetime_string = ""
    expiry_date_datetime_string = ""
    if(jobFields[DATE_POSTED] is not None):
        date_posted_datetime = dparser.parse(
            jobFields[DATE_POSTED], fuzzy=True)
        date_posted_datetime_string = date_posted_datetime.strftime(
            "%d-%m-%YT%H:%M:%S%z%Z")

        expiry_date_datetime = date_posted_datetime + \
            datetime.timedelta(days=EXPIRY_OFFSET)
        expiry_date_datetime_string = expiry_date_datetime.strftime(
            "%d-%m-%YT%H:%M:%S%z%Z")

    image_link = IMAGE_PREFIX_URL + jobFields[COMPANY][LOGO]
    jobDesc = json.dumps(jobFields[JOB_DESCRIPTION])

    # extract location from jobDescription
    locations = ",".join(jobFields[LOCATIONS])
    upperCaseJobDesc = jobDesc.upper()
    if len(jobFields[LOCATIONS]) == 0:
        for locn in LOCATIONS_LIST:
            if locn in upperCaseJobDesc:
                locations += locn + ","

    if len(locations) > 0 and locations[-1] == ",":
        locations = locations[:-1]

    # get rid of the location in JobDescription and the trailing unwanted text
    if len(jobDesc) > 0:
        if '<h4>' in jobDesc:
            index = jobDesc.index("<h4>")
            jobDesc = jobDesc[index:]
        rIndex = jobDesc.rfind("<p>")
        if rIndex != -1:
            jobDesc = jobDesc[:rIndex]

    jobLink = jobFields[EXTERNAL_URL]

    # replacing the query param value with techmaestro literal
    if len(jobLink) > 0 and '?' in jobLink:
        index = jobLink.index("?")
        firstPart = jobLink[:index]
        secondPart = jobLink[index:]
        secondPart = secondPart.replace("workattech", "techmaestro")
        jobLink = firstPart + secondPart

    date_opportunity = datetime.datetime.utcnow(
    ) + datetime.timedelta(days=OPPORTUNITY_OFFSET)

    if expiry_date_datetime_string == "":
        expiry_date_datetime = date_opportunity + \
            datetime.timedelta(days=EXPIRY_OFFSET - OPPORTUNITY_OFFSET)
        expiry_date_datetime_string = expiry_date_datetime.strftime(
            "%d-%m-%YT%H:%M:%S%z%Z")

    date_opportunity_string = date_opportunity.strftime(
        "%d-%m-%YT%H:%M:%S%z%Z")

    experience = ""

    if jobFields[EXPERIENCE][MIN] is not None:
        experience += "Min Experience : " + \
            str(jobFields[EXPERIENCE][MIN]) + ","
    if jobFields[EXPERIENCE][MAX] is not None:
        experience += "Max Experience : " + \
            str(jobFields[EXPERIENCE][MAX]) + ","
    if jobFields[EXPERIENCE][LEVEL] is not None and len(jobFields[EXPERIENCE][LEVEL]) > 0:
        experience += "Level : " + jobFields[EXPERIENCE][LEVEL]

    if len(experience) > 0 and experience[-1] == ",":
        experience = experience[:-1]

    # updatedOn same as createdOn apparently
    updatedOn = date_posted_datetime_string

    row = list([jobFields[COMPANY][NAME], date_posted_datetime_string, expiry_date_datetime_string, image_link,
               jobDesc.strip(), jobLink, locations, date_opportunity_string, experience, jobFields[TITLE], updatedOn])
    # print(row)
    # for i in range(len(row)):
    #     row[i] = row[i].decode("utf-8")
    return row


def addJobToCsv(job):
    jobId = job["id"]
    responseWithJobFields = requests.get(REQUREST_URL + "/" + jobId)
    jobFields = responseWithJobFields.json()
    row = getRowFromJobFields(jobFields)

    if os.path.isfile(CSV_FILE_REL_PATH):
        print("File exist so appending a row to CSV")
        # opening file in append mode
        with open(CSV_FILE_REL_PATH, 'a') as fp:
            writer = csv.writer(fp, delimiter=",")
            writer.writerow(row)

    else:
        print("File not exist so creating one")
        # creating a file and writing column header and first row
        with open(CSV_FILE_REL_PATH, 'w') as fp:
            writer = csv.writer(fp, delimiter=",")
            data = list()
            data.append(COLUMN_HEADERS)
            data.append(row)
            writer.writerows(data)
    return


def scrape():
    print("hell0")
    responseWithAllJobs = requests.get(REQUREST_URL)
    allJobs = responseWithAllJobs.json()
    count = 0
    for job in allJobs:
        if(count == 10):
            break
        addJobToCsv(job)
        count += 1
    print("############################################")
    print("Total jobs serialized --> " + str(count))
    return


if __name__ == "__main__":
    scrape()
