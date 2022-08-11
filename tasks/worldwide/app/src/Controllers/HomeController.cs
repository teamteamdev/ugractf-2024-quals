using Microsoft.AspNetCore.Mvc;

namespace pastapp.Controllers;

public class HomeController : Controller
{
    private readonly ILogger<HomeController> _logger;
    public HomeController(ILogger<HomeController> logger)
    {
        _logger = logger;
    }

    public IActionResult Index(string token)
    {
        ViewData["token"] = token;
        return View();
    }

}
