#!/usr/bin/env python3
"""
Links to Company News - Simple hard-coded Google News links
"""

from datetime import datetime, timezone

def get_company_news_links():
    """Return hard-coded company news links."""
    now = datetime.now(timezone.utc)
    
    companies = [
        {
            "name": "Cerebras Systems",
            "url": "https://www.google.com/search?biw=1194&bih=715&tbs=qdr%3Ad&tbm=nws&sxsrf=ALeKk03SEtD1M6ZgLet2K7RlC8cMTyrfng%3A1615518071879&ei=d9lKYM-hNcW2ggfI5p9o&q=cerebras+systems&oq=cerebras+systems&gs_lcp=Cg9tb2JpbGUtZ3dzLXNlcnAQARgAMgIIADICCAAyAggAMgIIADICCAA6BQgAELEDOgQIABADOggIABCxAxCDAVDtiwFYmZ8BYLKoAWgAcAB4AIABQYgBvgeSAQIxNpgBAKABAaoBGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOwAQDAAQE&sclient=mobile-gws-serp"
        },
        {
            "name": "Groq",
            "url": "https://www.google.com/search?q=groq&tbm=nws&prmd=nmsiv&sxsrf=ALeKk02hoSbw6xk2bZ2fgfBv43ktpgE56A:1628646306467&source=lnt&tbs=qdr:d&sa=X&biw=1194&bih=715&dpr=2&tbo=u&ved=2ahUKEwjcyYe74OWFAxWuFlkFHddjB3EQna4KKAJ6BAgKEAw"
        },
        {
            "name": "SambaNova Systems",
            "url": "https://www.google.com/search?q=sambanova+systems&sca_esv=251e5a0e8da88d6a&biw=402&bih=684&tbs=qdr%3Ad&tbm=nws&sxsrf=ADLYWIIwJAjUtkO98VThmEWPnKEPVBW7_A%3A1731097584720&ei=8HMuZ-fUK7KHkvQPqNGO8Aw&oq=sambanova%C2%A0&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiC3NhbWJhbm92YcKgKgIIADIOEAAYgAQYkQIYsQMYigUyBRAAGIAEMgUQABiABDILEAAYgAQYsQMYgwEyChAAGIAEGEMYigUyBRAAGIAEMgUQABiABDIFEAAYgARIhkxQiAlYuERwAHgAkAEAmAG8AaAB3w6qAQQ1LjExuAEByAEA-AEBigIZbW9iaWxlLWd3cy13aXotc2VycC1tb2Rlc5gCEKACnQ-oAgDCAg0QABiABBixAxhDGIoFwgIIEAAYgAQYsQPCAhAQABiABBixAxhDGIMBGIoFwgIOEAAYgAQYsQMYgwEYigWYAwKIBgGSBwQ0LjEyoAf2Pg&sclient=mobile-gws-serp"
        },
        {
            "name": "Neuralink",
            "url": "https://www.google.com/search?q=neuralink&sca_esv=4794ee3134a61051&biw=393&bih=665&tbs=qdr:d&tbm=nws&sxsrf=ACQVn08Bg29brfzKSV4dlbOtN0elzmsKDA:1706747879461&ei=5-e6ZZTVG92j5NoP86C_wAY&oq=nuera&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiBW51ZXJhKgIIADINEAAYgAQYChixAxiDATIQEAAYgAQYigUYChixAxiDATINEAAYgAQYChixAxiDATINEAAYgAQYChixAxiDATINEAAYgAQYChixAxiDATINEAAYgAQYChixAxiDATIQEAAYgAQYigUYChixAxiDATINEAAYgAQYChixAxiDAUihPlDkEliVM3AAeACQAQCYAU6gAboEqgEBObgBAcgBAPgBAYoCGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOoAgDCAhAQABiABBiKBRhDGLEDGIMBwgIFEAAYgATCAgcQABiABBgKwgIKEAAYgAQYigUYQ8ICCxAAGIAEGLEDGIMBwgIOEAAYgAQYigUYsQMYgwHCAggQABiABBixA8ICERAAGIAEGIoFGJECGLEDGIMBwgIXEAAYgAQYigUYkQIYsQMYgwEYsQMYgwGIBgE&sclient=mobile-gws-serp&tbo=u&sa=X&ved=2ahUKEwjjja2w84iEAxV5GFkFHbzKARgQna4KKAJ6BAgFEAw"
        },
        {
            "name": "Liquid Death",
            "url": "https://www.google.com/search?q=liquid+death&sca_esv=4794ee3134a61051&biw=393&bih=665&tbs=qdr%3Ad&tbm=nws&sxsrf=ACQVn096E6iICMLTU1NRQW0-JTthwjFE9w%3A1709516054171&ei=FiXlZaGNCsex5NoPqfSAoAM&oq=liquid+death&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiDGxpcXVpZCBkZWF0aDIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDILEAAYgAQYigUYkQIyBRAAGIAESJU-UKQRWKI1cAB4AJABAJgBSaAB0wWqAQIxNLgBA8gBAPgBAYoCGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOYAg6gApYGqAIAwgIIEAAYgAQYsQPCAg0QABiABBiKBRhDGLEDwgIKEAAYgAQYigUYQ8ICEBAAGIAEGIoFGEMYsQMYgwHCAgsQABiABBixAxiDAcICDhAAGIAEGIoFGJECGLEDwgIOEAAYgAQYigUYsQMYgwHCAgsQABiABBiKBRixA5gDAYgGAZIHAjE0&sclient=mobile-gws-serp"
        },
        {
            "name": "Automation Anywhere",
            "url": "https://www.google.com/search?q=automation+anywhere&sca_esv=a36b70f2ee78bb4e&biw=440&bih=766&tbs=qdr%3Ad&tbm=nws&sxsrf=ANbL-n44RJ49J4iut1ve8VtbrUwPOpEGdw%3A1772148327705&ei=Z9agabzbKtqh5NoPjPLi6QU&oq=automation+anywhere&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiE2F1dG9tYXRpb24gYW55d2hlcmUyDRAAGIAEGLEDGEMYigUyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAESNsUUABYAHAAeACQAQCYAUOgAXWqAQEyuAEDyAEAigIZbW9iaWxlLWd3cy13aXotc2VycC1tb2Rlc5gCAqACepgDAIgGAZIHATKgB-YIsgcBMrgHesIHBTAuMS4xyAcFgAgA&sclient=mobile-gws-serp"
        },
        {
            "name": "Impossible Foods",
            "url": "https://www.google.com/search?biw=1194&bih=715&tbs=qdr%3Ad&tbm=nws&sxsrf=ALeKk026OEtFVyxMyKdJnpYBVek3F9rCGQ%3A1615516330934&ei=qtJKYLu-OOLH_Qadl46ABA&q=impossible+foods&oq=imposs&gs_lcp=Cg9tb2JpbGUtZ3dzLXNlcnAQARgAMgIIADICCAAyAggAMgIIADICCAA6BQgAELEDUOR8WPqGAWCejAFoAHAAeACAATiIAcACkgEBNpgBAKABAaoBGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOwAQDAAQE&sclient=mobile-gws-serp"
        },
        {
            "name": "BitPay",
            "url": "https://www.google.com/search?q=bitpay&sca_esv=a36b70f2ee78bb4e&biw=440&bih=766&tbs=qdr%3Ad&tbm=nws&sxsrf=ANbL-n4izeOeyIwWILIxHTuAGlXUzhuw4Q%3A1772148405823&ei=tdagabz4Mfu15NoPhargqAU&oq=bitpay&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiBmJpdHBheTIIEAAYgAQYsQMyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAESMkaUKMIWOITcAB4AJABAJgBc6AByQSqAQMyLjS4AQPIAQD4AQGKAhltb2JpbGUtZ3dzLXdpei1zZXJwLW1vZGVzmAIGoALgBKgCAMICChAAGIAEGEMYigXCAg4QABiABBixAxiDARiKBcICCxAAGIAEGLEDGIMBwgILEAAYgAQYkQIYigXCAhAQABiABBixAxhDGIMBGIoFmAMDkgcDMi40oAfKF7IHAzIuNLgH4ATCBwMyLTbIBxWACAA&sclient=mobile-gws-serp"
        },
        {
            "name": "Dataminr",
            "url": "https://www.google.com/search?q=dataminr&biw=834&bih=1075&tbs=qdr%3Ad&tbm=nws&sxsrf=ALeKk0371uNYHOqh9sBIXNK7K4IUF_2jsw%3A1618351099625&ei=-xN2YIjJJaSz5NoPqOmO6As&oq=dataminr&gs_lcp=Cg9tb2JpbGUtZ3dzLXNlcnAQARgAMgIIADICCAAyAggAMgIIADICCAA6BQgAELEDOgYIABAKEANQ_ChYoTVgk0BoAHAAeACAAUaIAeMDkgEBOJgBAKABAaoBGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOwAQDAAQE&sclient=mobile-gws-serp"
        },
        {
            "name": "Mythic AI",
            "url": "https://www.google.com/search?q=mythic+ai&rlz=1C9BKJA_enUS592US592&hl=en-US&biw=1194&bih=715&tbs=qdr%3Ad&tbm=nws&sxsrf=ALeKk02yHvwilTchfbEKGcabCjuz1sfHbQ%3A1625102983686&ei=hxrdYL6jKe2E9PwPjMmQqAE&oq=mythic+ai&gs_lcp=Cg9tb2JpbGUtZ3dzLXNlcnAQAzICCAAyAggAMgIIADICCAAyAggAMgIIADICCAAyAggAOggIABCxAxCDAToFCAAQsQM6CAgAULEDEJECOgQIABAKUMtyWKaFAWDPiAFoAHAAeACAAT6IAd4DkgEBOJgBAKABAaoBGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOwAQDAAQE&sclient=mobile-gws-serp"
        },
        {
            "name": "Dialpad",
            "url": "https://www.google.com/search?q=dialpad&sca_esv=4794ee3134a61051&biw=440&bih=766&tbs=qdr%3Ad&tbm=nws&sxsrf=ANbL-n7y6SCfyIv2g1GFhg-bCNPKK8xZqQ%3A1772149008138&ei=ENmgaZiJCLnm5NoP1rXTuAo&oq=dialpad&gs_lp=Eg9tb2JpbGUtZ3dzLXNlcnAiB2RpYWxwYWQyCBAAGIAEGLEDMgsQABiABBixAxiDATIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABEi4MlDLCljnKnAAeACQAQGYAeEBoAHPDaoBBjE3LjIuMbgBA8gBAPgBAYoCGW1vYmlsZS1nd3Mtd2l6LXNlcnAtbW9kZXOYAhOgApgMqAIAwgIQEAAYgAQYsQMYgwEYigUYCsICBBAAGAPCAg0QABiABBixAxhDGIoFwgIOEAAYgAQYsQMYgwEYigXCAgoQABiABBhDGIoFmAMBiAYBkgcEMTcuMqAHjVSyBwQxNy4yuAeYDMIHCDEuMTUuMi4xyAcogAgA&sclient=mobile-gws-serp"
        },
    ]
    
    return {
        "title": "Links to Company News",
        "summary": f"{len(companies)} private companies — click to view recent Google News",
        "companies": companies,
        "meta": {
            "generated_at": now.isoformat(),
            "count": len(companies)
        }
    }


if __name__ == "__main__":
    import json
    result = get_company_news_links()
    print(json.dumps(result, indent=2))
