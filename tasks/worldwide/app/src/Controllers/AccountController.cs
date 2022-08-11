using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace pastapp.Controllers;

public class AccountController : Controller
{
    private readonly ILogger<AccountController> _logger;
    private const string _flagSecret = "ODZkNTY0Y2UtZjFhYy00MDRkLTljNjQt";
    private const string _flagPrefix = "ugra_localization_with_no_sanitazation_";
    private const int _suffixSize = 12;
    public AccountController(ILogger<AccountController> logger)
    {
        _logger = logger;
    }

    [Authorize]
    [AllowAnonymous]
    public IActionResult Index(string token)
    {
        if (!User.Identity.IsAuthenticated)
        {
            return Redirect($"/{token}/login/");
        }
        ViewData["token"] = token;
        var flag = GetFlag(token);
        return View((object)flag);
    }
    
    [NonAction]
    private string GetFlag(string token){
        return _flagPrefix + Convert.ToHexString(new HMACSHA256(Encoding.UTF8.GetBytes(_flagSecret)).ComputeHash(Encoding.UTF8.GetBytes(token)))[.._suffixSize].ToLower();
    }

}
