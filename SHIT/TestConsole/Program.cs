using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using GambaExtrasNamespace;
using HtmlAgilityPack;


namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {


            var tm = new GambaExtrasNamespace.TestMethods();
            HtmlAgilityPack.HtmlDocument doc;
            bool in_game = tm.GetLiveGame("euw","KobeeeeBryant", out doc);
            string to_print_string = tm.ParseDocToText(doc);

        }
    }
}
