using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using pastapp.Models;


namespace pastapp.Controllers;

public class LoginController : Controller
{
    ApplicationContext db;
    private readonly ILogger<LoginController> _logger;
    private readonly IConfiguration _config;
    public LoginController(ILogger<LoginController> logger, ApplicationContext context, IConfiguration config)
    {
        _logger = logger;
        db = context;
        _config = config;
    }

    [HttpGet]
    public IActionResult Index(string token, [FromQuery]bool? fail=false)
    {
        ViewData["token"] = token;
        if (User.Identity.IsAuthenticated){
            return Redirect($"/{token}/account/");
        }
        if ((bool)fail){
            ViewBag.ErrorMessage = "Invalid username or password. Please try again.";
        }
        return View();
    }

    [HttpPost]
    [Route("/{token}/login")]
    public async Task<IActionResult> Auth(string token, LoginViewModel data)
    {
        var user = await db.Users.Where(u => u.Username == data.Username).Where(u => u.Password == data.Password).FirstOrDefaultAsync();
        if (user != null){
            var securityKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_config["Jwt:Key"]));
            var credentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);

            var Sectoken = new JwtSecurityToken(_config["Jwt:Issuer"],
              expires: DateTime.Now.AddMinutes(120),
              signingCredentials: credentials);

            var session_token =  new JwtSecurityTokenHandler().WriteToken(Sectoken);
            Response.Cookies.Append("session", session_token, new CookieOptions { HttpOnly = true, SameSite = SameSiteMode.Strict });
            return Redirect($"/{token}/account/");
        }
        return Redirect($"/{token}/login/?fail=true");
    }
}