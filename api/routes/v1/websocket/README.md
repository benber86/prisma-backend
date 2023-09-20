# Websocket documentation


## Channels:
- troves_overview



<hr>


### troves_overview

Sample snapshot query:
```{
   "action":"snapshots",
   "channel":"troves_overview",
   "settings":[
      {
         "chain":"ethereum"
      }
   ]
}
```

Sample subscription query:

```{
   "action":"subscribe",
   "channel":"troves_overview",
   "settings":[
      {
         "chain":"ethereum"
      }
   ]
}
```

Sample response:

```{
   "channel":"troves_overview",
   "subscription":{
      "chain":"ethereum"
   },
   "type":"snapshot",
   "payload":[
      {
         "name":"wstETH",
         "address":"0xbf6883a03fd2fcfa1b9fc588ad6193b3c3178f8f",
         "tvl":17051851.782769278,
         "debt":9004049.574031109,
         "debt_cap":9000000.0,
         "cr":1.8937980785833424,
         "mcr":1.2,
         "rate":0.0,
         "price":1869.5054558781426,
         "open_troves":193,
         "closed_troves":9,
         "liq_troves":2,
         "red_troves":0
      },
      {
         "name":"rETH",
         "address":"0xe0e255fd5281bec3bb8fa1569a20097d9064e445",
         "tvl":16556562.328176232,
         "debt":8999728.194995085,
         "debt_cap":9000000.0,
         "cr":1.8396735956296593,
         "mcr":1.2,
         "rate":0.0,
         "price":1775.1566987678837,
         "open_troves":233,
         "closed_troves":6,
         "liq_troves":0,
         "red_troves":0
      },
      {
         "name":"sfrxETH",
         "address":"0xf69282a7e7ba5428f92f610e7afa1c0cedc4e483",
         "tvl":17165537.453514136,
         "debt":8999999.409701658,
         "debt_cap":9000000.0,
         "cr":1.9072820643755086,
         "mcr":1.2,
         "rate":0.0,
         "price":1730.4537870296201,
         "open_troves":125,
         "closed_troves":1,
         "liq_troves":0,
         "red_troves":0
      },
      {
         "name":"cbETH",
         "address":"0x63cc74334f4b1119276667cf0079ac0c8a96cfb2",
         "tvl":5344867.254454971,
         "debt":2999262.4119476383,
         "debt_cap":3000000.0,
         "cr":1.7820605603442887,
         "mcr":1.2,
         "rate":0.0,
         "price":1714.4884331341452,
         "open_troves":87,
         "closed_troves":7,
         "liq_troves":0,
         "red_troves":0
      },
      {
         "name":"cbETH",
         "address":"0x63cc74334f4b1119276667cf0079ac0c8a96cfb2",
         "tvl":5405766.336295028,
         "debt":2999996.061947638,
         "debt_cap":3000000.0,
         "cr":1.8019244774559906,
         "mcr":1.2,
         "rate":0.0,
         "price":1714.4884331341452,
         "open_troves":87,
         "closed_troves":7,
         "liq_troves":0,
         "red_troves":0
      }
   ]
}
```
