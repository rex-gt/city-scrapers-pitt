from city_scrapers_core.constants import NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

import re
from datetime import datetime

class CityPlanningSpider(CityScrapersSpider):
    name = "city_planning"
    agency = "City Of Pittsburgh Planning Commission Notices"
    timezone = "America/Chicago"
    allowed_domains = ["pittsburghpa.gov"]
    start_urls = ["http://pittsburghpa.gov/dcp/notices"]
    
    def _build_list(self,response):
        """
        Create list of events
        """
        everything = response.css('div.col-md-12').extract()[0]
        title_index = [m.start() for m in re.finditer('<p><strong>', everything)]
        events=[]
        for i in range(0,len(title_index)-1):
            start=title_index[i]
        #for the last event, need to make the end point just the end of everything
            if i ==len(title_index)-1:
                end=len(everything)-len('<p><strong>')
            else:
                end=title_index[i+1]-len('<p><strong>')
    
            events.append(everything[start:end])
            return events


    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        events=self._build_list(response)
        for item in events:
            meeting = Meeting(
                title=self._parse_title(item),
                description=self._parse_description(item),
                classification=self._parse_classification(item),
                start=self._parse_start(item),
                end=self._parse_end(item),
                all_day=self._parse_all_day(item),
                time_notes=self._parse_time_notes(item),
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title=re.search('<strong>(.*?)</strong>',item).group(1)
        return title

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return NOT_CLASSIFIED

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_text=re.search('\xa0(.*?)</li>',item).group(1)
        try:
            date = datetime.strptime(date_text, '%B %d, %Y %I:%M %p')
        except:
            try:
                date = datetime.strptime(date_text, '%B %d, %Y %I %p')
            except:
                date = datetime.datetime(1111, 11, 11)
        return date

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return None

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):
        """Parse or generate location."""
        e2=item[re.search('<li>(.*?)</li>',item).end():]
        location=re.search('<li>(.*?)</li>',e2).group(1)
        """test if the location starts with a number"""
        if bool(re.search("^[0-9]",location)):
            location_name=""
            address=location
        else:
            location_name=re.search('^(.+?),',location).group(1)
            address=re.search('^'+address+', '+'(.*?)$',location).group(1)
            location={"name":location_name,"address":address}
        return location

    def _parse_links(self, item):
        e2=item[re.search('<li>(.*?)</li>',item).end():]
        href=re.findall('href="(.*?)"', e2)
        title=re.findall('"_blank">(.*?)</a>', e2)
        links=[]
        for n in range(0, len(href)):
            links.append({"href": href[n], "title": title[n]})
        return links

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
