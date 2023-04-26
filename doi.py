import codecs
from datacite import schema42
import json
import re
import sys
import urllib.request as urlreq
from urllib.parse import quote

#Converted EZID python cli:
# https://github.com/CDLUC3/ezid-client-tools/blob/049ab655c6149f3ef7ae91576971092ed02e1d44/ezid3.py

class MyHTTPErrorProcessor (urlreq.HTTPErrorProcessor):
  def http_response (self, request, response):
    # Bizarre that Python leaves this out.
    if response.code == 201:
      return response
    else:
      return urlreq.HTTPErrorProcessor.http_response(self, request, response)
  https_response = http_response

class EZID():
    def __init__(self, username, password, server = "https://ezid.cdlib.org"):
        self._username = username
        self._password = password
        self._server = server
        self._base_doi_url = "https://ezid.cdlib.org/id/"
        self._opener = urlreq.build_opener(MyHTTPErrorProcessor())
        self.update_opener()
        self.Datacite = Datacite()
        self.Sage = Sage()

    def format_anvl_request(self, metadata_json, metada_profile="datacite"):
        metadata_xml = self.Datacite.convert_to_xml(metadata_json)
        metadata_xml = re.sub("[%\r\n]", lambda c: "%%%02X" % ord(c.group(0)), metadata_xml)
        request = ["%s: %s" % (metada_profile, metadata_xml)]
        return "\n".join(request)

    def update_opener(self):
        h = urlreq.HTTPBasicAuthHandler()
        h.add_password("EZID", self._server, self._username, self._password)
        self._opener.add_handler(h)

    def issue_request(self, path, method, data):
        request = urlreq.Request(self._server + path)
        request.get_method = lambda: method
        request.add_header("Content-Type", "text/plain; charset=UTF-8")
        request.data = data.encode("UTF-8")
        try:
            connection = self._opener.open(request)
            response = connection.read()
            return response.decode("UTF-8")
        except urlreq.HTTPError as e:
            print(f"code: {e.code}, message: {e.msg}\n")
            sys.stderr.write(response)
            sys.exit(1)

    def encode(self,id):
        return quote(id, ":/")
    
    def issue_doi(self,json_file,shoulder,start_date,end_date,pkgs):
       metadata_dict = self.Datacite.load_json_file(json_file)
       metadata_dict = self.Sage.update_metadata(metadata_dict,start_date,end_date,pkgs)
       postPayload = self.format_anvl_request(metadata_dict)
       path = "/shoulder/"+self.encode(shoulder)
       response = self.issue_request(path, "POST", postPayload)
       doi = response.split()[1]
       doi_url = self._base_doi_url + doi
       return doi_url

class Datacite():
    def load_json_file(self,json_file):
        with open(json_file, 'r') as file:
            jsonData=file.read()
        metadata = json.loads(jsonData)
        self.is_valid(metadata)
        return metadata

    def is_valid(self,metadata):
        assert schema42.validate(metadata), 'Invalid JSON file.'

    def convert_to_xml(self,metadata):
       return schema42.tostring(metadata)

class Sage():
    def __init__(self):
        self.lcrc_base_url = "https://web.lcrc.anl.gov/public/waggle/sagedata/"

    def update_dates(self,start_date,end_date):
        dates = [
        {
            "date": start_date,
            "dateType": "Created"
        },
        {
            "date": start_date,
            "dateType": "Available"
        },
        {
            "date": start_date+"/"+end_date,
            "dateType": "Collected"
        }]
        return dates

    def base_related_identifier(self,pkg):
        return {
            "relatedIdentifier": self.lcrc_base_url+pkg,
            "relatedIdentifierType": "URL",
            "relationType": "Describes"
        }

    def update_related_identifiers(self,pkgs):
        identifiers = []
        for pkg in pkgs:
            identifiers.append(self.base_related_identifier(pkg))
        return identifiers

    def update_metadata(self,metadataJson,start_date,end_date,pkgs):
        metadataJson['publicationYear'] = str(start_date.year)
        metadataJson['dates'] = self.update_dates(str(start_date),str(end_date))
        metadataJson['relatedIdentifiers'] = self.update_related_identifiers(pkgs)
        return metadataJson
