using HtmlAgilityPack;
using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using System.Collections;
using System.Text.RegularExpressions;

namespace GambaExtrasNamespace
{
    public class TestMethods
    {
        public int PrintToConsole(string message)
        {
            Console.WriteLine("C# .NET Core DLL says: " + message);
            return 123;
        }

        /// <summary>
        /// creates a string,string dictionary which is parsed to json
        /// </summary>
        /// <param name="doc"></param>
        /// <returns></returns>
        public string ParseDocToText(HtmlAgilityPack.HtmlDocument doc)
        {
            var live_game_box_node = doc.DocumentNode.SelectSingleNode("/div/div");
            Dictionary<string,string> dictionary = new Dictionary<string, string>();
            var datetime_node = live_game_box_node.SelectSingleNode("/div[1]");
            dictionary.Add("GameStartTime", live_game_box_node.SelectSingleNode("div[1]/small[2]/span").InnerText);
            var blue_team_node = live_game_box_node.SelectSingleNode("div[2]/table[1]/tbody");
            var red_team_node = live_game_box_node.SelectSingleNode("div[2]/table[2]/tbody");
            Dictionary<bool,List<HtmlNode>> player_nodes = new Dictionary<bool, List<HtmlNode>>();
            player_nodes.Add(true, new List<HtmlNode>(blue_team_node.SelectNodes("tr")));
            player_nodes.Add(false, new List<HtmlNode>(red_team_node.SelectNodes("tr")));
            Dictionary<bool,string> side_string = new Dictionary<bool, string>()
            {
                [true]="Blue_",
                [false] = "Red_",
            };
            Dictionary<int,string> pos_string = new Dictionary<int, string>()
            {
                [0]="Top_",
                [1] = "Jun_",
                [2]="Mid_",
                [3] = "Adc_",
                [4]="Sup_",
                
            };
            foreach(var side_blue in new bool[]{ true,false})
            {
                for(int i_pos = 0; i_pos < player_nodes[side_blue].Count; i_pos++)
                {
                    var cur_player_node = player_nodes[side_blue][i_pos];
                    var cur_prefix=  side_string[side_blue] + pos_string[i_pos];
                    dictionary.Add(cur_prefix+"Champion", TryGetStat(cur_player_node,"td[1]/a","title"));
                    dictionary.Add(cur_prefix+"Player", TryGetStat(cur_player_node, "td[4]/a"));
                    dictionary.Add(cur_prefix+"Rank", TryGetStat(cur_player_node, "td[6]/div"));
                    dictionary.Add(cur_prefix+"Winrate", TryGetStat(cur_player_node, "td[7]/span") + ", " +
                                                            TryGetStat(cur_player_node, "td[7]/span[2]"));
                    dictionary.Add(cur_prefix+"ChampionWinrate", TryGetStat(cur_player_node, "td[8]/div/span") + ", " +
                                                            TryGetStat(cur_player_node, "td[8]/div/span[2]"));
                    dictionary.Add(cur_prefix+"ChampionKDA", TryGetStat(cur_player_node, "td[9]/text()[2]"));
                }
            }
            return Newtonsoft.Json.JsonConvert.SerializeObject(dictionary);
        }

        private string TryGetStat(HtmlNode player_node, string xpath, string att_val="")
        {
            var subnode = player_node.SelectSingleNode(xpath);//.GetAttributeValue("title", "")
            if(subnode==null)
                return "";
            if(att_val=="")
                return Regex.Replace(subnode.InnerText,"[\\t\\n\\r]","");
            else
            {
                return subnode.GetAttributeValue(att_val, "");
            }
        }

        public string LiveGameJsonDict(string region, string summoner_name)
        {
            if(GetLiveGame(region, summoner_name, out HtmlAgilityPack.HtmlDocument doc))
            {
                return ParseDocToText(doc);
            }
            else
                return "";
        }

        /// <summary>
        /// returns false if game not live.
        /// </summary>
        /// <param name="region"></param>
        /// <param name="summoner_name"></param>
        /// <param name="doc"></param>
        /// <returns></returns>
        public bool GetLiveGame(string region, string summoner_name, out HtmlAgilityPack.HtmlDocument doc)
        {
            string html;
            string query = @"https://" + region + @".op.gg/summoner/ajax/spectator3/summonerName=" + summoner_name +@"&force=true";
            HttpClientHandler ch = new HttpClientHandler();
            ch.UseDefaultCredentials = true;
            HttpClient client = new HttpClient(ch);
            doc = new HtmlAgilityPack.HtmlDocument();
            client.DefaultRequestHeaders.ConnectionClose = false;
            string response_text="";
            try
            {
                HttpRequestMessage request = new HttpRequestMessage(HttpMethod.Post, query)
                {
                    Content = new StringContent("a"),
                    //Version = HttpVersion.Version10
                };
                
                Thread.Sleep(100);
                
                HttpResponseMessage response=null;
                Task.Run(async () => {
                    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12;
                    response = await client.SendAsync(request);
                }).Wait();
               
                //HttpResponseMessage response = client.SendAsync(request).Result;
                //HttpResponseMessage response = await client.GetAsync(query_string);
                Thread.Sleep(50);
                
                response.EnsureSuccessStatusCode();
                

                Task.Run(async () => { response_text = await response.Content.ReadAsStringAsync(); }).Wait();
                doc.LoadHtml(response_text);
                return true;
            }
            catch(Exception e)
            {
                return false;
            }
            
        }

        public string TestRekkles()
        {
            string html;


            string query = @"https://euw.op.gg/summoner/ajax/spectator3/summonerName=MagiFelix5&force=true";//Config.HTML.RequestGamesURLOPGG(m_server, summoner_to_query.ID.ToString());

            

            HttpClientHandler ch = new HttpClientHandler();
            ch.UseDefaultCredentials = true;

            //query_string = @"http://euw.op.gg/summoner/matches/ajax/averageAndList/startInfo=0&summonerId=99996851&type=soloranked";
            //query_string = @"https://app.mobalytics.gg/api/lol/summoners/v1/EUW/Astr0Perro/overview";
            HttpClient client = new HttpClient(ch);

            client.DefaultRequestHeaders.ConnectionClose = false;
            string response_text="";
            int location=0;
            try
            {
                /*var _cur_time = DateTime.Now;
                var _time_since_last = Convert.ToInt32((_cur_time - m_lastQueryTime).TotalMilliseconds);
                var _time_since_last_any = Convert.ToInt32((_cur_time - Config.LastQueryTime).TotalMilliseconds);
                bool _waited = false;
                if(_time_since_last < Config.InThreadHtmlMinBreakBetweenQueriesInMs)
                {
                    Thread.Sleep(Config.InThreadHtmlMinBreakBetweenQueriesInMs - _time_since_last);
                    _waited = true;
                }
                if(_time_since_last_any<Config.OutOfThreadHtmlMinBReakBetweenQueriesInMs)
                {
                    Thread.Sleep(Config.OutOfThreadHtmlMinBReakBetweenQueriesInMs - _time_since_last_any);
                    _waited = true;
                }

                */

                HttpRequestMessage request = new HttpRequestMessage(HttpMethod.Post, query)
                {
                    Content = new StringContent("a"),
                    //Version = HttpVersion.Version10
                };
                location=1;
                Thread.Sleep(100);
                location=2;
                HttpResponseMessage response=null;
                Task.Run(async () => {
                    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12;
                    response = await client.SendAsync(request); 
                }).Wait();
                location=3;
                //HttpResponseMessage response = client.SendAsync(request).Result;
                //HttpResponseMessage response = await client.GetAsync(query_string);
                Thread.Sleep(50);
                location=4;
                response.EnsureSuccessStatusCode();
                location=5;

                Task.Run(async () => { response_text = await response.Content.ReadAsStringAsync(); }).Wait();
                location=6;
                //response_text = response.Content.ReadAsStringAsync().Result;
                //response_text = await response.Content.ReadAsStringAsync();
                //Config.LastQueryTime = DateTime.Now;
            }
            catch(Exception e)
            {

                response_text = "shit failed after loc" + location.ToString() +" ,: " + e.InnerException.Message;// + e.Message;
                
                /*response_text = "";
                if(e.Message.Contains("403"))
                {
                    CrashFromForbidden = true;
                    throw new Exception("Forbidden, end all");
                }
                if(e.Message.Contains("418"))
                {
                    //DEBUG.MinorErrorLog("HTML query failed: 418");
                    //-> this means we have got all the games / the server doesnt want to give any older ajax games
                    Thread.Sleep(200);
                }
                else
                {
                    string err_string = "HTML query failed: " + e.Message;
                    if(e.InnerException != null)
                        err_string += ": " + e.InnerException.Message;
                    DEBUG.ErrorLog(err_string);
                    Thread.Sleep(5000);
                    if(e.Message.Contains("429"))
                    {
                        DEBUG.ErrorLog("Timing out for 300s due to 429 (" + Thread.CurrentThread.ManagedThreadId.ToString() + ")");
                        Thread.Sleep(300000);
                    }
                    if(e.InnerException!= null
                        && e.InnerException.Message == "Unable to read data from the transport connection: The connection was closed.")
                    {
                        DEBUG.ErrorLog("Timing out for 120s due to Ajax additional games being down (" + Thread.CurrentThread.ManagedThreadId.ToString() + ")");
                        Thread.Sleep(120000);
                    }
                }*/
            }

            ch.Dispose();
            client.Dispose(); 



            return response_text;

        }
    }
}
